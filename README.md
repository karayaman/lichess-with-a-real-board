# Lichess with a real board
Software that enables you to connect your real life chess board to [Lichess.org](https://lichess.org/) . Using computer vision it will detect the moves you make on your chess board. After that, if it's your turn to move in the online game, it will send your move to Lichess servers using [Lichess Board API](https://lichess.org/blog/XlRW5REAAB8AUJJ-/welcome-lichess-boards) . It can also record or transcribe your over-the-board games as PGN, so they can be broadcast using  [Lichess Broadcaster](https://lichess.org/broadcast/app) .  This project is Lichess-only version of my project [Play online chess with real chess board](https://github.com/karayaman/Play-online-chess-with-real-chess-board) .

## GUI

You need to run the GUI to do the steps in Setup, Usage, Broadcast, Transcribe and Diagnostic sections and customize how you use the software.

![](https://github.com/karayaman/lichess-with-a-real-board/raw/main/gui.jpg)

## Setup

1. Generate a  [Lichess API Access Token](https://lichess.org/account/oauth/token/create?scopes[]=board:play&description=Lichess+with+a+real+board). Then, enter the token to the GUI.
2. Place your webcam near to your chessboard so that all of the squares and pieces can be clearly seen by it.
3. Select a board calibration mode and follow its instructions.

## Board Calibration(The board is empty.)

1. Remove all pieces from your chess board.

2. Click the "Board Calibration" button.

3. Check that corners of your chess board are correctly detected and press key "q" to save detected chess board corners. You don't need to manually select chess board corners; it should be automatically detected by the program. The upper left square, which is covered by points (0,0), (0,1),(1,0) and (1,1) should be a8. You can rotate the image by pressing the key "r" to adjust that. Example chess board detection result:

   <img src="https://github.com/karayaman/lichess-with-a-real-board/raw/main/chessboard_detection_result.jpg" style="zoom:67%;" />

## Board Calibration(Pieces are in their starting positions.)

1. Place the pieces in their starting positions.
2. Click the "Board Calibration" button.
3. Please ensure your chess board is correctly positioned and detected. Guiding lines will be drawn to mark the board's edges:
   - The line near the white pieces will be blue.
   - The line near the black pieces will be green.
   - Press any key to exit once you've confirmed the board setup.

<img src="https://github.com/karayaman/lichess-with-a-real-board/raw/main/board_detection_result.jpg" style="zoom:67%;" />

## Board Calibration(Just before the game starts.)

1. Click the "Start Game" button. The software will calibrate the board just before it begins move recognition.

## Usage

1. Place pieces of the chess board to their starting position.
2. Start the Lichess game.
3. Click the "Start Game" button.
4. Wait until it says "game started".
5. Make your move if it's your turn, otherwise make your opponent's move.
6. Notice that it actually makes your move in the Lichess game, if it's your turn. Otherwise, wait until it says the starting and ending squares of the opponent's move. To save clock time, you may choose not to wait, but this is not recommended.
7. Go to step 5.

## Broadcast

1. Switch to the "Broadcast" tab and select the folder where PGN files will be saved. Also, select the same folder in the  [Lichess Broadcaster](https://lichess.org/broadcast/app) .

2. Enter the name of the PGN.

3. Fill in the PGN metadata.

4. Place pieces of the chess board to their starting position.

5. Click the "Start Game" button.

6. The players can now start playing, and the software will update the PGN after each move.

7. After the game ends, stop the software and assign the result of the game.

   <img src="https://github.com/karayaman/lichess-with-a-real-board/blob/main/broadcastgui.jpg?raw=true" style="zoom:67%;" />

## Transcribe

1. Switch to the "Transcribe" tab and select the video file to be transcribed.

2. Select the folder where PGN files will be saved. Also, select the same folder in the  [Lichess Broadcaster](https://lichess.org/broadcast/app) .

3. Enter the name of the PGN.

4. Fill in the PGN metadata.

5. Click the "Start Game" button.

6. The software will update the PGN after each move it transcribes.

7. After the software finishes the transcription, assign the result of the game.

   <img src="https://github.com/karayaman/lichess-with-a-real-board/blob/main/transcribegui.jpg?raw=true" style="zoom:67%;" />

## Diagnostic

You need to click the "Diagnostic" button to run the diagnostic process. It will show your chessboard in a perspective-transformed form, exactly as the software sees it. Additionally, it will mark white pieces with a blue circle and black pieces with a green circle, allowing you to verify if the software can detect the pieces on the chess board.

![](https://github.com/karayaman/lichess-with-a-real-board/blob/main/diagnostic.jpg?raw=true)

## Required libraries

- opencv-python
- python-chess
- numpy
- pyttsx3
- scikit-image
- pygrabber
- berserk

