import time

import chess
import cv2
import numpy as np
import pickle
import os
import sys
from helper import detect_state, get_square_image, predict
from lichess_game import Lichess_game
from lichess_commentator import Lichess_commentator
import chess.pgn


class Game:
    def __init__(self, board_basics, speech_thread, comment_me,
                 comment_opponent, language, token, roi_mask, is_broadcast, pgn_path):
        if token:
            self.internet_game = Lichess_game(token)
        elif is_broadcast:
            self.internet_game = None
            self.pgn_path = pgn_path
        else:
            print("Please enter your Lichess API Access Token.")
            sys.exit(0)
        self.is_broadcast = is_broadcast
        self.board_basics = board_basics
        self.speech_thread = speech_thread
        self.executed_moves = []
        self.played_moves = []
        self.board = chess.Board()
        self.comment_me = comment_me
        self.comment_opponent = comment_opponent
        self.language = language
        self.roi_mask = roi_mask
        self.hog = cv2.HOGDescriptor((64, 64), (16, 16), (8, 8), (8, 8), 9)
        self.knn = cv2.ml.KNearest_create()
        self.features = None
        self.labels = None
        self.save_file = 'hog.bin'
        self.piece_model = cv2.dnn.readNetFromONNX("cnn_piece.onnx")
        self.color_model = cv2.dnn.readNetFromONNX("cnn_color.onnx")
        
        if is_broadcast:
            self.commentator = None
        else:
            commentator_thread = Lichess_commentator()
            commentator_thread.daemon = True
            commentator_thread.stream = self.internet_game.client.board.stream_game_state(self.internet_game.game_id)
            commentator_thread.speech_thread = self.speech_thread
            commentator_thread.game_state.we_play_white = self.internet_game.we_play_white
            commentator_thread.game_state.game = self
            commentator_thread.comment_me = self.comment_me
            commentator_thread.comment_opponent = self.comment_opponent
            commentator_thread.language = self.language
            self.commentator = commentator_thread

    def initialize_hog(self, frame):
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        pieces = []
        squares = []
        for row in range(8):
            for column in range(8):
                square_name = self.board_basics.convert_row_column_to_square_name(row, column)
                square = chess.parse_square(square_name)
                piece = self.board.piece_at(square)
                square_image = get_square_image(row, column, frame)
                square_image = cv2.resize(square_image, (64, 64))
                if piece:
                    pieces.append(square_image)
                else:
                    squares.append(square_image)
        pieces_hog = [self.hog.compute(piece) for piece in pieces]
        squares_hog = [self.hog.compute(square) for square in squares]
        labels_pieces = np.ones((len(pieces_hog), 1), np.int32)
        labels_squares = np.zeros((len(squares_hog), 1), np.int32)
        pieces_hog = np.array(pieces_hog)
        squares_hog = np.array(squares_hog)
        features = np.float32(np.concatenate((pieces_hog, squares_hog), axis=0))
        labels = np.concatenate((labels_pieces, labels_squares), axis=0)
        self.knn.train(features, cv2.ml.ROW_SAMPLE, labels)
        self.features = features
        self.labels = labels

        outfile = open(self.save_file, 'wb')
        pickle.dump([features, labels], outfile)
        outfile.close()

    def load_hog(self):
        if os.path.exists(self.save_file):
            infile = open(self.save_file, 'rb')
            self.features, self.labels = pickle.load(infile)
            infile.close()
            self.knn.train(self.features, cv2.ml.ROW_SAMPLE, self.labels)
        else:
            print("You need to play at least 1 game before starting a game from position.")
            sys.exit(0)

    def detect_state_hog(self, chessboard_image):
        chessboard_image = cv2.cvtColor(chessboard_image, cv2.COLOR_BGR2GRAY)
        chessboard = [[get_square_image(row, column, chessboard_image) for column in range(8)] for row
                      in
                      range(8)]

        board_hog = [[self.hog.compute(cv2.resize(chessboard[row][column], (64, 64))) for column in range(8)] for row
                     in
                     range(8)]
        knn_result = []
        for row in range(8):
            knn_row = []
            for column in range(8):
                ret, result, neighbours, dist = self.knn.findNearest(np.array([board_hog[row][column]]), k=3)
                knn_row.append(result[0][0])
            knn_result.append(knn_row)
        board_state = [[knn_result[row][column] > 0.5 for column in range(8)] for row
                       in
                       range(8)]
        return board_state

    def detect_state_cnn(self, chessboard_image):
        state = []
        for row in range(8):
            row_state = []
            for column in range(8):
                height, width = chessboard_image.shape[:2]
                minX = int(column * width / 8)
                maxX = int((column + 1) * width / 8)
                minY = int(row * height / 8)
                maxY = int((row + 1) * height / 8)
                square_image = chessboard_image[minY:maxY, minX:maxX]
                is_piece = predict(square_image, self.piece_model)
                if is_piece:
                    is_white = predict(square_image, self.color_model)
                    if is_white:
                        row_state.append('w')
                    else:
                        row_state.append('b')
                else:
                    row_state.append('.')
            state.append(row_state)
        return state

    def check_state_cnn(self, result):
        for row in range(8):
            for column in range(8):
                square_name = self.board_basics.convert_row_column_to_square_name(row, column)
                square = chess.parse_square(square_name)
                piece = self.board.piece_at(square)
                expected_state = '.'
                if piece:
                    if piece.color == chess.WHITE:
                        expected_state = 'w'
                    else:
                        expected_state = 'b'

                if result[row][column] != expected_state:
                    return False
        return True

    def get_valid_2_move_cnn(self, frame):
        board_result = self.detect_state_cnn(frame)

        move_to_register = self.get_move_to_register()

        if move_to_register:
            self.board.push(move_to_register)            
            for move in self.board.legal_moves:                    
                if move.promotion and move.promotion != chess.QUEEN:
                    continue
                self.board.push(move)
                if self.check_state_cnn(board_result):
                    self.board.pop()
                    valid_move_string = move_to_register.uci()
                    self.speech_thread.put_text(valid_move_string[:4])
                    self.played_moves.append(move_to_register)
                    self.board.pop()
                    self.executed_moves.append(self.board.san(move_to_register))
                    self.board.push(move_to_register)
                    if self.internet_game:
                        self.internet_game.is_our_turn = not self.internet_game.is_our_turn
                    print(f"First move is {valid_move_string}")
                    return True, move.uci()
                else:
                    self.board.pop()
            self.board.pop()
        elif self.is_broadcast:
            for move in list(self.board.legal_moves):                    
                if move.promotion and move.promotion != chess.QUEEN:
                    continue
                self.board.push(move)
                for other_move in list(self.board.legal_moves):
                    if other_move.promotion and other_move.promotion != chess.QUEEN:
                        continue
                    self.board.push(other_move)
                    if self.check_state_cnn(board_result):
                        self.board.pop()
                        valid_move_string = move.uci()
                        self.played_moves.append(move)
                        self.board.pop()
                        self.executed_moves.append(self.board.san(move))
                        self.board.push(move)
                        print(f"First move is {valid_move_string}")
                        return True, other_move.uci()
                    self.board.pop()
                self.board.pop()
        return False, ""

    def get_valid_move_cnn(self, frame):
        board_result = self.detect_state_cnn(frame)

        move_to_register = self.get_move_to_register()

        if move_to_register:
            self.board.push(move_to_register)
            if self.check_state_cnn(board_result):
                self.board.pop()
                return True, move_to_register.uci()
            else:
                self.board.pop()
                return False, ""
        else:
            for move in self.board.legal_moves:                    
                if move.promotion and move.promotion != chess.QUEEN:
                    continue
                self.board.push(move)
                if self.check_state_cnn(board_result):
                    self.board.pop()
                    return True, move.uci()
                else:
                    self.board.pop()
        return False, ""

    def get_valid_move_hog(self, fgmask, frame):
        board = [[self.board_basics.get_square_image(row, column, fgmask).mean() for column in range(8)] for row in
                 range(8)]
        potential_squares = []
        square_scores = {}
        for row in range(8):
            for column in range(8):
                score = board[row][column]
                if score < 10.0:
                    continue
                square_name = self.board_basics.convert_row_column_to_square_name(row, column)
                square = chess.parse_square(square_name)
                potential_squares.append(square)
                square_scores[square] = score

        move_to_register = self.get_move_to_register()
        potential_moves = []

        board_result = self.detect_state_hog(frame)
        if move_to_register:
            if (move_to_register.from_square in potential_squares) and (
                    move_to_register.to_square in potential_squares):
                self.board.push(move_to_register)
                if self.check_state_hog(board_result):
                    self.board.pop()
                    return True, move_to_register.uci()
                else:
                    self.board.pop()
                    return False, ""
        else:
            for move in self.board.legal_moves:
                if (move.from_square in potential_squares) and (move.to_square in potential_squares):
                    if move.promotion and move.promotion != chess.QUEEN:
                        continue
                    self.board.push(move)
                    if self.check_state_hog(board_result):
                        self.board.pop()
                        total_score = square_scores[move.from_square] + square_scores[move.to_square]
                        potential_moves.append((total_score, move.uci()))
                    else:
                        self.board.pop()
        if potential_moves:
            return True, max(potential_moves)[1]
        else:
            return False, ""

    def get_move_to_register(self):
        if self.commentator:
            if len(self.executed_moves) < len(self.commentator.game_state.registered_moves):
                return self.commentator.game_state.registered_moves[len(self.executed_moves)]
            else:
                return None
        else:
            return None

    def is_light_change(self, frame):
        state = False
        if self.roi_mask is not None:
            result = detect_state(frame, self.board_basics.d[0], self.roi_mask)
            result_hog = self.detect_state_hog(frame)
            state = self.check_state_for_light(result, result_hog)
        if state:
            print("Light change")
            return True
        else:
            result_cnn = self.detect_state_cnn(frame)
            state_cnn = self.check_state_cnn(result_cnn)
            if state_cnn:
                print("Light change cnn")
            return state_cnn

    def check_state_hog(self, result):
        for row in range(8):
            for column in range(8):
                square_name = self.board_basics.convert_row_column_to_square_name(row, column)
                square = chess.parse_square(square_name)
                piece = self.board.piece_at(square)
                if piece and (not result[row][column]):
                    print("Expected piece at " + square_name)
                    return False
                if (not piece) and (result[row][column]):
                    print("Expected empty at " + square_name)
                    return False
        return True

    def check_state_for_move(self, result):
        for row in range(8):
            for column in range(8):
                square_name = self.board_basics.convert_row_column_to_square_name(row, column)
                square = chess.parse_square(square_name)
                piece = self.board.piece_at(square)
                if piece and (True not in result[row][column]):
                    print("Expected piece at " + square_name)
                    return False
                if (not piece) and (False not in result[row][column]):
                    print("Expected empty at " + square_name)
                    return False
        return True

    def check_state_for_light(self, result, result_hog):
        for row in range(8):
            for column in range(8):
                if len(result[row][column]) > 1:
                    result[row][column] = [result_hog[row][column]]
                square_name = self.board_basics.convert_row_column_to_square_name(row, column)
                square = chess.parse_square(square_name)
                piece = self.board.piece_at(square)
                if piece and (False in result[row][column]):
                    print(square_name)
                    return False
                if (not piece) and (True in result[row][column]):
                    print(square_name)
                    return False
        return True

    def get_valid_move_canny(self, fgmask, frame):
        if self.roi_mask is None:
            return False, ""
        board = [[self.board_basics.get_square_image(row, column, fgmask).mean() for column in range(8)] for row in
                 range(8)]
        potential_squares = []
        square_scores = {}
        for row in range(8):
            for column in range(8):
                score = board[row][column]
                if score < 10.0:
                    continue
                square_name = self.board_basics.convert_row_column_to_square_name(row, column)
                square = chess.parse_square(square_name)
                potential_squares.append(square)
                square_scores[square] = score

        move_to_register = self.get_move_to_register()
        potential_moves = []

        board_result = detect_state(frame, self.board_basics.d[0], self.roi_mask)
        if move_to_register:
            if (move_to_register.from_square in potential_squares) and (
                    move_to_register.to_square in potential_squares):
                self.board.push(move_to_register)
                if self.check_state_for_move(board_result):
                    self.board.pop()
                    return True, move_to_register.uci()
                else:
                    self.board.pop()
                    return False, ""
        else:
            for move in self.board.legal_moves:
                if (move.from_square in potential_squares) and (move.to_square in potential_squares):
                    if move.promotion and move.promotion != chess.QUEEN:
                        continue
                    self.board.push(move)
                    if self.check_state_for_move(board_result):
                        self.board.pop()
                        total_score = square_scores[move.from_square] + square_scores[move.to_square]
                        potential_moves.append((total_score, move.uci()))
                    else:
                        self.board.pop()
        if potential_moves:
            return True, max(potential_moves)[1]
        else:
            return False, ""

    def register_move(self, fgmask, previous_frame, next_frame):
        success, valid_move_string = self.get_valid_2_move_cnn(next_frame)
        if not success:
            success, valid_move_string = self.get_valid_move_cnn(next_frame)
            if not success:
                potential_squares, potential_moves = self.board_basics.get_potential_moves(fgmask, previous_frame,
                                                                                           next_frame,
                                                                                           self.board)
                success, valid_move_string = self.get_valid_move(potential_squares, potential_moves)
                if not success:
                    success, valid_move_string = self.get_valid_move_canny(fgmask, next_frame)
                    
                    if not success:
                        success, valid_move_string = self.get_valid_move_hog(fgmask, next_frame)
                        if not success:
                            self.speech_thread.put_text(self.language.move_failed)
                            print(self.board.fen())
                            return False
                        else:
                            print("Valid move string 5:" + valid_move_string)
                    else:
                        print("Valid move string 4:" + valid_move_string)
                else:
                    print("Valid move string 3:" + valid_move_string)
            else:
                print("Valid move string 2:" + valid_move_string)
        else:
            print("Valid move string 1:" + valid_move_string)

        valid_move_UCI = chess.Move.from_uci(valid_move_string)

        if self.internet_game and self.internet_game.is_our_turn:
            self.internet_game.move(valid_move_UCI)
            self.played_moves.append(valid_move_UCI)
            while self.commentator:
                time.sleep(0.1)
                move_to_register = self.get_move_to_register()
                if move_to_register:
                    valid_move_UCI = move_to_register
                    break
        else:
            self.speech_thread.put_text(valid_move_string[:4])
            self.played_moves.append(valid_move_UCI)

        self.executed_moves.append(self.board.san(valid_move_UCI))
        is_capture = self.board.is_capture(valid_move_UCI)
        color = int(self.board.turn)
        self.board.push(valid_move_UCI)
        self.update_pgn()
        if self.internet_game:
            self.internet_game.is_our_turn = not self.internet_game.is_our_turn

        self.learn(next_frame)
        self.board_basics.update_ssim(previous_frame, next_frame, valid_move_UCI, is_capture, color)
        return True

    def update_pgn(self):
        if not self.is_broadcast:
            return
        with open(self.pgn_path) as pgn_file:
            pgn_game = chess.pgn.read_game(pgn_file)

        updated_game = chess.pgn.Game()
        updated_game.headers = pgn_game.headers

        moves = list(self.board.move_stack)

        node = updated_game
        for move in moves:
            node = node.add_variation(move)

        with open(self.pgn_path, "w") as pgn_file:
            exporter = chess.pgn.FileExporter(pgn_file)
            updated_game.accept(exporter)

    def learn(self, frame):
        result = self.detect_state_hog(frame)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        new_pieces = []
        new_squares = []

        for row in range(8):
            for column in range(8):
                square_name = self.board_basics.convert_row_column_to_square_name(row, column)
                square = chess.parse_square(square_name)
                piece = self.board.piece_at(square)
                if piece and (not result[row][column]):
                    print("Learning piece at " + square_name)
                    piece_hog = self.hog.compute(cv2.resize(get_square_image(row, column, frame), (64, 64)))
                    new_pieces.append(piece_hog)
                if (not piece) and (result[row][column]):
                    print("Learning empty at " + square_name)
                    square_hog = self.hog.compute(cv2.resize(get_square_image(row, column, frame), (64, 64)))
                    new_squares.append(square_hog)
        labels_pieces = np.ones((len(new_pieces), 1), np.int32)
        labels_squares = np.zeros((len(new_squares), 1), np.int32)
        if new_pieces:
            new_pieces = np.array(new_pieces)
            self.features = np.float32(np.concatenate((self.features, new_pieces), axis=0))
            self.labels = np.concatenate((self.labels, labels_pieces), axis=0)
        if new_squares:
            new_squares = np.array(new_squares)
            self.features = np.float32(np.concatenate((self.features, new_squares), axis=0))
            self.labels = np.concatenate((self.labels, labels_squares), axis=0)

        self.features = self.features[:100]
        self.labels = self.labels[:100]
        self.knn = cv2.ml.KNearest_create()
        self.knn.train(self.features, cv2.ml.ROW_SAMPLE, self.labels)

    def get_valid_move(self, potential_squares, potential_moves):
        print("Potential squares")
        print(potential_squares)
        print("Potential moves")
        print(potential_moves)

        move_to_register = self.get_move_to_register()

        valid_move_string = ""
        for score, start, arrival in potential_moves:
            if valid_move_string:
                break

            if move_to_register:
                if chess.square_name(move_to_register.from_square) != start:
                    continue
                if chess.square_name(move_to_register.to_square) != arrival:
                    continue

            uci_move = start + arrival
            try:
                move = chess.Move.from_uci(uci_move)
            except Exception as e:
                print(e)
                continue

            if move in self.board.legal_moves:
                valid_move_string = uci_move
            else:
                if move_to_register:
                    uci_move_promoted = move_to_register.uci()
                else:
                    uci_move_promoted = uci_move + 'q'
                promoted_move = chess.Move.from_uci(uci_move_promoted)
                if promoted_move in self.board.legal_moves:
                    valid_move_string = uci_move_promoted
                    # print("There has been a promotion")

        potential_squares = [square[1] for square in potential_squares]
        print(potential_squares)
        # Detect castling king side with white
        if ("e1" in potential_squares) and ("h1" in potential_squares) and ("f1" in potential_squares) and (
                "g1" in potential_squares) and (chess.Move.from_uci("e1g1") in self.board.legal_moves):
            valid_move_string = "e1g1"

        # Detect castling queen side with white
        if ("e1" in potential_squares) and ("a1" in potential_squares) and ("c1" in potential_squares) and (
                "d1" in potential_squares) and (chess.Move.from_uci("e1c1") in self.board.legal_moves):
            valid_move_string = "e1c1"

        # Detect castling king side with black
        if ("e8" in potential_squares) and ("h8" in potential_squares) and ("f8" in potential_squares) and (
                "g8" in potential_squares) and (chess.Move.from_uci("e8g8") in self.board.legal_moves):
            valid_move_string = "e8g8"

        # Detect castling queen side with black
        if ("e8" in potential_squares) and ("a8" in potential_squares) and ("c8" in potential_squares) and (
                "d8" in potential_squares) and (chess.Move.from_uci("e8c8") in self.board.legal_moves):
            valid_move_string = "e8c8"

        if move_to_register and (move_to_register.uci() != valid_move_string):
            return False, valid_move_string

        if valid_move_string:
            return True, valid_move_string
        else:
            return False, valid_move_string
