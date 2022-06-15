# Lichess with a real board
Software that enables you to connect your real life chess board to [Lichess.org](https://lichess.org/) . Using computer vision it will detect the moves you make on your chess board. After that, if it's your turn to move in the online game, it will send your move to Lichess servers using [Lichess Board API](https://lichess.org/blog/XlRW5REAAB8AUJJ-/welcome-lichess-boards) . This project is Lichess-only version of my project [Play online chess with real chess board](https://github.com/karayaman/Play-online-chess-with-real-chess-board) .

## GUI

You need to run the GUI to do the steps in Setup and Usage sections and customize how you use the software.

![](https://github.com/karayaman/lichess-with-a-real-board/raw/main/gui.jpg)

## Setup

1. Generate a  [Lichess API Access Token](https://lichess.org/account/oauth/token/create?scopes[]=board:play&description=Lichess+with+a+real+board). Then, enter the token to the GUI.

2. Place your webcam near to your chessboard so that all of the squares and pieces can be clearly seen by it.

3. Remove all pieces from your chess board.

4. Click "Board Calibration" button.

5. Check that corners of your chess board are correctly detected and press key "q" to save detected chess board corners. You don't need to manually select chess board corners; it should be automatically detected by the program. The upper left square, which is covered by points (0,0), (0,1),(1,0) and (1,1) should be a8. You can rotate the image by pressing the key "r" to adjust that. Example chess board detection result:

   <img src="https://github.com/karayaman/lichess-with-a-real-board/raw/main/chessboard_detection_result.jpg" style="zoom:67%;" />

## Usage

1. Place pieces of the chess board to their starting position.
2. Start the Lichess game.
3. Click "Start Game" button.
5.  Wait until it says "game started".
6. Make your move if it's your turn, otherwise make your opponent's move.
8. Notice that it actually makes your move in the Lichess game, if it's your turn. Otherwise, wait until it says the starting and ending squares of the opponent's move. 
9. Go to step 5.

## Required libraries

- opencv-python
- python-chess
- numpy
- pyttsx3
- scikit-image
- pygrabber
- mac-say
- berserk
