import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import filedialog
import subprocess
import sys
from threading import Thread
import pickle
import os
import chess
import chess.pgn

running_process = None


def on_closing():
    if running_process:
        if running_process.poll() is None:
            running_process.terminate()
    save_settings()
    window.destroy()


def log_process(process, finish_message):
    global button_frame
    button_stop = tk.Button(button_frame, text="Stop", command=stop_process)
    button_stop.grid(row=0, column=0, columnspan=3, sticky="ew")
    while True:
        output = process.stdout.readline()
        if output:
            logs_text.insert(tk.END, output.decode())
        if process.poll() is not None:
            logs_text.insert(tk.END, finish_message)
            break
    global start, board
    start = tk.Button(button_frame, text="Start Game", command=start_game)
    start.grid(row=0, column=0)
    board = tk.Button(button_frame, text="Board Calibration", command=board_calibration)
    board.grid(row=0, column=1)
    diagnostic_button = tk.Button(button_frame, text="Diagnostic", command=diagnostic)
    diagnostic_button.grid(row=0, column=2)
    if promotion_menu.cget("state") == "normal":
        promotion.set(PROMOTION_OPTIONS[0])
        promotion_menu.configure(state="disabled")


def stop_process(ignore=None):
    if running_process:
        if running_process.poll() is None:
            running_process.terminate()


def diagnostic(ignore=None):
    selected_tab = notebook.index(notebook.select())
    arguments = [sys.executable, "diagnostic.py"]
    # arguments = ["diagnostic.exe"]
    # working_directory = sys.argv[0][:-3]
    # arguments = [working_directory+"diagnostic"]
    selected_camera = camera.get()
    if selected_camera != OPTIONS[0]:
        cap_index = OPTIONS.index(selected_camera) - 1
        arguments.append("cap=" + str(cap_index))
    selected_resolution = resolution.get()
    if selected_resolution != RESOLUTION_OPTIONS[0]:
        width, height = selected_resolution.split(" x ")
        arguments.append(f"width={width}")
        arguments.append(f"height={height}")
    selected_fps = fps.get()
    if selected_fps != FPS_OPTIONS[0]:
        arguments.append(f"fps={selected_fps}")
    if (calibration_mode.get() == CALIBRATION_OPTIONS[-1]) or (selected_tab == 2):
        arguments.append("calibrate")
    if selected_tab == 2:
        arguments.append("vpath=" + video_file.get())
    process = subprocess.Popen(arguments, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    # startupinfo = subprocess.STARTUPINFO()
    # startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    # process = subprocess.Popen(arguments, stdout=subprocess.PIPE,
    #                           stderr=subprocess.STDOUT, stdin=subprocess.PIPE, startupinfo=startupinfo)
    # process = subprocess.Popen(arguments, stdout=subprocess.PIPE,
    #                           stderr=subprocess.STDOUT, cwd=working_directory)
    global running_process
    running_process = process
    log_thread = Thread(target=log_process, args=(process, "Diagnostic finished.\n"))
    log_thread.daemon = True
    log_thread.start()


def board_calibration(ignore=None):
    selected_tab = notebook.index(notebook.select())
    if selected_tab == 2 or calibration_mode.get() == CALIBRATION_OPTIONS[-1]:
        if selected_tab == 2:
            messagebox.showinfo(
                "Board Calibration Not Required",
                "Calibration is not necessary for the video transcription process. "
                "You can proceed directly without calibration."
            )
        else:
            messagebox.showinfo(
                "Board Calibration Not Required",
                "Calibration is not necessary for this mode. "
                "You can proceed directly without calibration."
            )
        return

    arguments = [sys.executable, "board_calibration.py", "show-info"]
    # arguments = ["board_calibration.exe", "show-info"]
    # working_directory = sys.argv[0][:-3]
    # arguments = [working_directory+"board_calibration", "show-info"]
    selected_camera = camera.get()
    if selected_camera != OPTIONS[0]:
        cap_index = OPTIONS.index(selected_camera) - 1
        arguments.append("cap=" + str(cap_index))
    selected_resolution = resolution.get()
    if selected_resolution != RESOLUTION_OPTIONS[0]:
        width, height = selected_resolution.split(" x ")
        arguments.append(f"width={width}")
        arguments.append(f"height={height}")
    selected_fps = fps.get()
    if selected_fps != FPS_OPTIONS[0]:
        arguments.append(f"fps={selected_fps}")
    if calibration_mode.get() == CALIBRATION_OPTIONS[-1]:
        return
    elif calibration_mode.get() == CALIBRATION_OPTIONS[1]:
        arguments.append("ml")
    process = subprocess.Popen(arguments, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
    # startupinfo = subprocess.STARTUPINFO()
    # startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    # process = subprocess.Popen(arguments, stdout=subprocess.PIPE,
    #                           stderr=subprocess.STDOUT, stdin=subprocess.PIPE, startupinfo=startupinfo)
    # process = subprocess.Popen(arguments, stdout=subprocess.PIPE,
    #                           stderr=subprocess.STDOUT, cwd=working_directory)
    global running_process
    running_process = process
    log_thread = Thread(target=log_process, args=(process, "Board calibration finished.\n"))
    log_thread.daemon = True
    log_thread.start()


def start_game(ignore=None):
    arguments = [sys.executable, "main.py"]
    # arguments = ["main.exe"]
    # working_directory = sys.argv[0][:-3]
    # arguments = [working_directory+"main"]
    selected_camera = camera.get()
    if selected_camera != OPTIONS[0]:
        cap_index = OPTIONS.index(selected_camera) - 1
        arguments.append("cap=" + str(cap_index))
    selected_resolution = resolution.get()
    if selected_resolution != RESOLUTION_OPTIONS[0]:
        width, height = selected_resolution.split(" x ")
        arguments.append(f"width={width}")
        arguments.append(f"height={height}")
    selected_fps = fps.get()
    if selected_fps != FPS_OPTIONS[0]:
        arguments.append(f"fps={selected_fps}")
    selected_tab = notebook.index(notebook.select())
    if (calibration_mode.get() == CALIBRATION_OPTIONS[-1]) or (selected_tab == 2):
        arguments.append("calibrate")

    if selected_tab == 0:
        if comment_me.get():
            arguments.append("comment-me")
        if comment_opponent.get():
            arguments.append("comment-opponent")
        if token.get():
            arguments.append("token=" + token.get())
        promotion_menu.configure(state="normal")
        promotion.set(PROMOTION_OPTIONS[0])

        selected_voice = voice.get()
        if selected_voice != VOICE_OPTIONS[0]:
            voice_index = VOICE_OPTIONS.index(selected_voice) - 1
            arguments.append("voice=" + str(voice_index))
            language = "English"
            languages = ["English", "German", "Russian", "Turkish", "Italian", "French"]
            codes = ["en_", "de_", "ru_", "tr_", "it_", "fr_"]
            for l, c in zip(languages, codes):
                if (l in selected_voice) or (l.lower() in selected_voice) or (c in selected_voice):
                    language = l
                    break
            arguments.append("lang=" + language)
    else:
        if selected_tab == 2:
            arguments.append("vpath=" + video_file.get())

        pgn_path = os.path.join(pgn_folder.get(), f'{pgn_name.get()}.pgn')
        arguments.append(f"pgn={pgn_path}")

        chess_game = chess.pgn.Game()

        for pgn_tag, pgn_tag_var in pgn_tag_mapping.items():
            pgn_tag_value = pgn_tag_var.get()
            if pgn_tag_value:
                chess_game.headers[pgn_tag] = pgn_tag_value

        # Save the game as a PGN file
        with open(pgn_path, "w") as pgn_file:
            exporter = chess.pgn.FileExporter(pgn_file)
            chess_game.accept(exporter)

    process = subprocess.Popen(arguments, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # startupinfo = subprocess.STARTUPINFO()
    # startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    # process = subprocess.Popen(arguments, stdout=subprocess.PIPE,
    #                           stderr=subprocess.STDOUT, stdin=subprocess.PIPE, startupinfo=startupinfo)
    # process = subprocess.Popen(arguments, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, cwd=working_directory)
    global running_process
    running_process = process
    log_thread = Thread(target=log_process, args=(process, "Game finished.\n"))
    log_thread.daemon = True
    log_thread.start()


window = tk.Tk()
window.title("Lichess with a real board by Alper Karayaman")

notebook = ttk.Notebook(window)
play_frame = tk.Frame(notebook)
notebook.grid(column=0, row=0, sticky=tk.W)

token = tk.StringVar()
comment_me = tk.IntVar()
comment_opponent = tk.IntVar()

token_frame = tk.Frame(play_frame)
token_frame.grid(row=0, column=0, columnspan=2, sticky="W")
label = tk.Label(token_frame, text='Lichess API Access Token:')
label.grid(column=0, row=0, sticky=tk.W)
token_entry = tk.Entry(token_frame, textvariable=token, width=24, show='*')
token_entry.grid(column=1, row=0, sticky=tk.W)

menu_frame = tk.Frame(play_frame)
menu_frame.grid(row=1, column=0, columnspan=2, sticky="W")
camera = tk.StringVar()
OPTIONS = ["Default"]
try:
    import platform

    platform_name = platform.system()
    if platform_name == "Darwin":
        cmd = 'system_profiler SPCameraDataType | grep "^    [^ ]" | sed "s/    //" | sed "s/://"'
        result = subprocess.check_output(cmd, shell=True)
        result = result.decode()
        result = [r for r in result.split("\n") if r]
        OPTIONS.extend(result)
    elif platform_name == "Linux":
        cmd = 'for I in /sys/class/video4linux/*; do cat $I/name; done'
        result = subprocess.check_output(cmd, shell=True)
        result = result.decode()
        result = [r for r in result.split("\n") if r]
        OPTIONS.extend(result)
    else:
        from pygrabber.dshow_graph import FilterGraph

        OPTIONS.extend(FilterGraph().get_input_devices())
except:
    pass
camera.set(OPTIONS[0])
label = tk.Label(menu_frame, text='Select Webcam:')
label.grid(column=0, row=0, sticky=tk.W)
menu = tk.OptionMenu(menu_frame, camera, *OPTIONS)
menu.config(width=max(len(option) for option in OPTIONS), anchor="w")
menu.grid(column=1, row=0, sticky=tk.W)

resolution_frame = tk.Frame(play_frame)
resolution_frame.grid(row=2, column=0, columnspan=2, sticky="W")
resolution = tk.StringVar()
RESOLUTION_OPTIONS = ["Default", "640 x 480", "1280 x 720", "1920 x 1080", "2560 x 1440", "3840 x 2160"]
resolution.set(RESOLUTION_OPTIONS[0])
resolution_label = tk.Label(resolution_frame, text='Select Webcam Resolution:')
resolution_label.grid(column=0, row=0, sticky=tk.W)
resolution_menu = tk.OptionMenu(resolution_frame, resolution, *RESOLUTION_OPTIONS)
resolution_menu.config(width=max(len(option) for option in RESOLUTION_OPTIONS), anchor="w")
resolution_menu.grid(column=1, row=0, sticky=tk.W)

fps_frame = tk.Frame(play_frame)
fps_frame.grid(row=3, column=0, columnspan=2, sticky="W")
fps = tk.StringVar()
FPS_OPTIONS = ["Default", "15", "24", "30", "60", "120", "144", "240"]
fps.set(FPS_OPTIONS[0])
fps_label = tk.Label(fps_frame, text='Select Webcam FPS:')
fps_label.grid(column=0, row=0, sticky=tk.W)
fps_menu = tk.OptionMenu(fps_frame, fps, *FPS_OPTIONS)
fps_menu.config(width=max(len(option) for option in FPS_OPTIONS), anchor="w")
fps_menu.grid(column=1, row=0, sticky=tk.W)


calibration_frame = tk.Frame(play_frame)
calibration_frame.grid(row=4, column=0, columnspan=2, sticky="W")
calibration_mode = tk.StringVar()
CALIBRATION_OPTIONS = ["The board is empty.", "Pieces are in their starting positions.",
                       "Just before the game starts."]
calibration_mode.set(CALIBRATION_OPTIONS[0])
calibration_label = tk.Label(calibration_frame, text='Board Calibration Mode:')
calibration_label.grid(column=0, row=0, sticky=tk.W)
calibration_menu = tk.OptionMenu(calibration_frame, calibration_mode, *CALIBRATION_OPTIONS)
calibration_menu.config(width=max(len(option) for option in CALIBRATION_OPTIONS), anchor="w")
calibration_menu.grid(column=1, row=0, sticky=tk.W)

voice_frame = tk.Frame(play_frame)
voice_frame.grid(row=5, column=0, columnspan=2, sticky="W")
voice = tk.StringVar()
VOICE_OPTIONS = ["Default"]
try:
    import platform

    if platform.system() == "Darwin":
        result = subprocess.run(['say', '-v', '?'], stdout=subprocess.PIPE)
        output = result.stdout.decode('utf-8')
        for line in output.splitlines():
            if line:
                voice_info = line.split()
                VOICE_OPTIONS.append(f'{voice_info[0]} {voice_info[1]}')
    else:
        import pyttsx3

        engine = pyttsx3.init()
        for v in engine.getProperty('voices'):
            VOICE_OPTIONS.append(v.name)
except:
    pass
voice.set(VOICE_OPTIONS[0])
voice_label = tk.Label(voice_frame, text='Select Voice:')
voice_label.grid(column=0, row=0, sticky=tk.W)
voice_menu = tk.OptionMenu(voice_frame, voice, *VOICE_OPTIONS)
voice_menu.config(width=max(len(option) for option in VOICE_OPTIONS), anchor="w")
voice_menu.grid(column=1, row=0, sticky=tk.W)


def save_promotion(*args):
    outfile = open("promotion.bin", 'wb')
    pickle.dump(promotion.get(), outfile)
    outfile.close()


def save_pgn_result(*args):
    pgn_path = os.path.join(pgn_folder.get(), f'{pgn_name.get()}.pgn')
    if not os.path.exists(pgn_path):
        return

    with open(pgn_path) as pgn_file:
        chess_game = chess.pgn.read_game(pgn_file)

    chess_game.headers["Result"] = pgn_result.get()

    with open(pgn_path, "w") as modified_pgn:
        exporter = chess.pgn.FileExporter(modified_pgn)
        chess_game.accept(exporter)


promotion_frame = tk.Frame(play_frame)
promotion_frame.grid(row=6, column=0, columnspan=2, sticky="W")
promotion = tk.StringVar()
promotion.trace("w", save_promotion)
PROMOTION_OPTIONS = ["Queen", "Knight", "Rook", "Bishop"]
promotion.set(PROMOTION_OPTIONS[0])
promotion_label = tk.Label(promotion_frame, text='Select Promotion Piece:')
promotion_label.grid(column=0, row=0, sticky=tk.W)
promotion_menu = tk.OptionMenu(promotion_frame, promotion, *PROMOTION_OPTIONS)
promotion_menu.config(width=max(len(option) for option in PROMOTION_OPTIONS), anchor="w")
promotion_menu.grid(column=1, row=0, sticky=tk.W)
promotion_menu.configure(state="disabled")

c2 = tk.Checkbutton(play_frame, text="Speak my moves.", variable=comment_me)
c2.grid(row=7, column=0, sticky="W", columnspan=1)

c3 = tk.Checkbutton(play_frame, text="Speak opponent's moves.", variable=comment_opponent)
c3.grid(row=8, column=0, sticky="W", columnspan=1)

button_frame = tk.Frame(window)
button_frame.grid(row=1, column=0, columnspan=3, sticky="W")
start = tk.Button(button_frame, text="Start Game", command=start_game)
start.grid(row=0, column=0)
board = tk.Button(button_frame, text="Board Calibration", command=board_calibration)
board.grid(row=0, column=1)
diagnostic_button = tk.Button(button_frame, text="Diagnostic", command=diagnostic)
diagnostic_button.grid(row=0, column=2)
text_frame = tk.Frame(window)
text_frame.grid(row=2, column=0)
scroll_bar = tk.Scrollbar(text_frame)
logs_text = tk.Text(text_frame, background='gray', yscrollcommand=scroll_bar.set)
scroll_bar.config(command=logs_text.yview)
scroll_bar.pack(side=tk.RIGHT, fill=tk.Y)
logs_text.pack(side="left")

fields = [comment_me, comment_opponent, calibration_mode, resolution, fps, camera, voice, token]
save_file = 'gui.bin'


def save_settings():
    outfile = open(save_file, 'wb')
    variables = [field.get() for field in fields]
    pgn_variables = [pgn_folder.get(), pgn_name.get()] + [pgn_tag_mapping[pgn_tag].get() for pgn_tag in pgn_tag_list]
    pickle.dump((variables, pgn_variables), outfile)
    outfile.close()


def load_settings():
    if os.path.exists(save_file):
        infile = open(save_file, 'rb')
        variables, pgn_values = pickle.load(infile)
        infile.close()
        token.set(variables[-1])
        if variables[-2] in VOICE_OPTIONS:
            voice.set(variables[-2])

        if variables[-3] in OPTIONS:
            camera.set(variables[-3])

        for i in range(5):
            fields[i].set(variables[i])

        pgn_variables = [pgn_folder, pgn_name] + [pgn_tag_mapping[pgn_tag] for pgn_tag in pgn_tag_list]
        for pgn_variable, pgn_tag_value in zip(pgn_variables, pgn_values):
            pgn_variable.set(pgn_tag_value)

        for pgn_folder_label in pgn_folder_label_list:
            pgn_folder_label.config(text=pgn_folder.get())


pgn_folder = tk.StringVar()
pgn_folder.set("No folder selected")

video_file = tk.StringVar()
video_file.set("No video file selected")


def select_folder():
    folder_path = filedialog.askdirectory()
    if folder_path:
        pgn_folder.set(folder_path)
        for pgn_folder_label in pgn_folder_label_list:
            pgn_folder_label.config(text=folder_path)


def select_video():
    file_path = filedialog.askopenfilename(
        title="Select a Video File",
        filetypes=[
            ("Video Files", "*.mp4 *.avi *.mov *.mkv *.flv *.webm"),
            ("All Files", "*.*")
        ]
    )
    if file_path:
        video_file.set(file_path)
        video_file_label.config(text=file_path)


broadcast_frame = ttk.Frame(notebook)
transcribe_frame = ttk.Frame(notebook)

video_file_frame = tk.Frame(transcribe_frame)
video_file_frame.grid(row=0, column=0, columnspan=2, sticky="W")
video_file_button = tk.Button(video_file_frame, text="Select Video File", command=select_video)
video_file_button.grid(column=0, row=0, sticky=tk.W)
video_file_label = tk.Label(video_file_frame, text=video_file.get())
video_file_label.grid(column=1, row=0, sticky=tk.W)

pgn_name = tk.StringVar()
pgn_tag_list = [
    "Event",
    "Site",
    "Date",
    "Time",
    "TimeControl",
    "Mode",
    "Round",
    "White",
    "Black",
    "WhiteElo",
    "BlackElo",
]
pgn_tag_mapping = {}
for i, pgn_tag in enumerate(pgn_tag_list):
    pgn_tag_var = tk.StringVar()
    pgn_tag_mapping[pgn_tag] = pgn_tag_var
pgn_result = tk.StringVar()
pgn_result.trace("w", save_pgn_result)
PGN_RESULT_OPTIONS = ["*", "1-0", "0-1", "1/2-1/2"]
pgn_result.set(PGN_RESULT_OPTIONS[0])
pgn_folder_label_list = []

for i, frame in enumerate((broadcast_frame, transcribe_frame)):
    pgn_folder_frame = tk.Frame(frame)
    pgn_folder_frame.grid(row=0 + i, column=0, columnspan=2, sticky="W")
    pgn_folder_button = tk.Button(pgn_folder_frame, text="Select PGN Folder", command=select_folder)
    pgn_folder_button.grid(column=0, row=0, sticky=tk.W)
    pgn_folder_label = tk.Label(pgn_folder_frame, text=pgn_folder.get())
    pgn_folder_label.grid(column=1, row=0, sticky=tk.W)
    pgn_folder_label_list.append(pgn_folder_label)

    pgn_name_frame = tk.Frame(frame)
    pgn_name_frame.grid(row=1 + i, column=0, columnspan=2, sticky="W")
    pgn_name_label = tk.Label(pgn_name_frame, text='PGN name:')
    pgn_name_label.grid(column=0, row=0, sticky=tk.W)
    pgn_name_entry = tk.Entry(pgn_name_frame, textvariable=pgn_name, width=30)
    pgn_name_entry.grid(column=1, row=0, sticky=tk.W)

    for j, pgn_tag in enumerate(pgn_tag_list):
        pgn_tag_var = pgn_tag_mapping[pgn_tag]
        pgn_tag_frame = tk.Frame(frame)
        pgn_tag_frame.grid(row=i + j + 2, column=0, columnspan=2, sticky="W")
        pgn_tag_label = tk.Label(pgn_tag_frame, text=f'{pgn_tag}:')
        pgn_tag_label.grid(column=0, row=0, sticky=tk.W)
        pgn_tag_entry = tk.Entry(pgn_tag_frame, textvariable=pgn_tag_var, width=30)
        pgn_tag_entry.grid(column=1, row=0, sticky=tk.W)

    pgn_result_frame = tk.Frame(frame)
    pgn_result_frame.grid(row=i + 2 + len(pgn_tag_list), column=0, columnspan=2, sticky="W")
    pgn_result_label = tk.Label(pgn_result_frame, text='Result:')
    pgn_result_label.grid(column=0, row=0, sticky=tk.W)
    pgn_result_menu = tk.OptionMenu(pgn_result_frame, pgn_result, *PGN_RESULT_OPTIONS)
    pgn_result_menu.config(width=max(len(option) for option in PGN_RESULT_OPTIONS), anchor="w")
    pgn_result_menu.grid(column=1, row=0, sticky=tk.W)

notebook.add(play_frame, text="Play")
notebook.add(broadcast_frame, text="Broadcast")
notebook.add(transcribe_frame, text="Transcribe")

load_settings()

window.protocol("WM_DELETE_WINDOW", on_closing)
window.mainloop()
