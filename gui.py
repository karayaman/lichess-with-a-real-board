import tkinter as tk
import subprocess
import sys
from threading import Thread
import pickle
import os

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
    button_stop.grid(row=0, column=0, columnspan=2, sticky="ew")
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
    if promotion_menu.cget("state") == "normal":
        promotion.set(PROMOTION_OPTIONS[0])
        promotion_menu.configure(state="disabled")


def stop_process(ignore=None):
    if running_process:
        if running_process.poll() is None:
            running_process.terminate()


def board_calibration(ignore=None):
    arguments = [sys.executable, "board_calibration.py", "show-info"]
    # arguments = ["board_calibration.exe", "show-info"]
    # working_directory = sys.argv[0][:-3]
    # arguments = [working_directory+"board_calibration", "show-info"]
    selected_camera = camera.get()
    if selected_camera != OPTIONS[0]:
        cap_index = OPTIONS.index(selected_camera) - 1
        arguments.append("cap=" + str(cap_index))
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
    if comment_me.get():
        arguments.append("comment-me")
    if comment_opponent.get():
        arguments.append("comment-opponent")
    if token.get():
        arguments.append("token=" + token.get())
    promotion_menu.configure(state="normal")
    promotion.set(PROMOTION_OPTIONS[0])

    selected_camera = camera.get()
    if selected_camera != OPTIONS[0]:
        cap_index = OPTIONS.index(selected_camera) - 1
        arguments.append("cap=" + str(cap_index))

    selected_voice = voice.get()
    if selected_voice != VOICE_OPTIONS[0]:
        voice_index = VOICE_OPTIONS.index(selected_voice) - 1
        arguments.append("voice=" + str(voice_index))
        language = "English"
        languages = ["English", "German", "Russian", "Turkish", "Italian"]
        codes = ["en_", "de_", "ru_", "tr_", "it_"]
        for l, c in zip(languages, codes):
            if (l in selected_voice) or (l.lower() in selected_voice) or (c in selected_voice):
                language = l
                break
        arguments.append("lang=" + language)
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

token = tk.StringVar()
comment_me = tk.IntVar()
comment_opponent = tk.IntVar()

token_frame = tk.Frame(window)
token_frame.grid(row=0, column=0, columnspan=2, sticky="W")
label = tk.Label(token_frame, text='Lichess API Access Token:')
label.grid(column=0, row=0, sticky=tk.W)
token_entry = tk.Entry(token_frame, textvariable=token, width=24, show='*')
token_entry.grid(column=1, row=0, sticky=tk.W)

menu_frame = tk.Frame(window)
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
label = tk.Label(menu_frame, text='Webcam to be used:')
label.grid(column=0, row=0, sticky=tk.W)
menu = tk.OptionMenu(menu_frame, camera, *OPTIONS)
menu.config(width=max(len(option) for option in OPTIONS), anchor="w")
menu.grid(column=1, row=0, sticky=tk.W)

voice_frame = tk.Frame(window)
voice_frame.grid(row=2, column=0, columnspan=2, sticky="W")
voice = tk.StringVar()
VOICE_OPTIONS = ["Default"]
try:
    import platform

    if platform.system() == "Darwin":
        import mac_say

        for v in mac_say.voices():
            VOICE_OPTIONS.append(v[0] + " " + v[1])
    else:
        import pyttsx3

        engine = pyttsx3.init()
        for v in engine.getProperty('voices'):
            VOICE_OPTIONS.append(v.name)
except:
    pass
voice.set(VOICE_OPTIONS[0])
voice_label = tk.Label(voice_frame, text='Voice preference:')
voice_label.grid(column=0, row=0, sticky=tk.W)
voice_menu = tk.OptionMenu(voice_frame, voice, *VOICE_OPTIONS)
voice_menu.config(width=max(len(option) for option in VOICE_OPTIONS), anchor="w")
voice_menu.grid(column=1, row=0, sticky=tk.W)


def save_promotion(*args):
    outfile = open("promotion.bin", 'wb')
    pickle.dump(promotion.get(), outfile)
    outfile.close()


promotion_frame = tk.Frame(window)
promotion_frame.grid(row=3, column=0, columnspan=2, sticky="W")
promotion = tk.StringVar()
promotion.trace("w", save_promotion)
PROMOTION_OPTIONS = ["Queen", "Knight", "Rook", "Bishop"]
promotion.set(PROMOTION_OPTIONS[0])
promotion_label = tk.Label(promotion_frame, text='Promotion piece:')
promotion_label.grid(column=0, row=0, sticky=tk.W)
promotion_menu = tk.OptionMenu(promotion_frame, promotion, *PROMOTION_OPTIONS)
promotion_menu.config(width=max(len(option) for option in PROMOTION_OPTIONS), anchor="w")
promotion_menu.grid(column=1, row=0, sticky=tk.W)
promotion_menu.configure(state="disabled")

c2 = tk.Checkbutton(window, text="Speak my moves.", variable=comment_me)
c2.grid(row=4, column=0, sticky="W", columnspan=1)

c3 = tk.Checkbutton(window, text="Speak opponent's moves.", variable=comment_opponent)
c3.grid(row=5, column=0, sticky="W", columnspan=1)

button_frame = tk.Frame(window)
button_frame.grid(row=6, column=0, columnspan=2, sticky="W")
start = tk.Button(button_frame, text="Start Game", command=start_game)
start.grid(row=0, column=0)
board = tk.Button(button_frame, text="Board Calibration", command=board_calibration)
board.grid(row=0, column=1)
text_frame = tk.Frame(window)
text_frame.grid(row=7, column=0)
scroll_bar = tk.Scrollbar(text_frame)
logs_text = tk.Text(text_frame, background='gray', yscrollcommand=scroll_bar.set)
scroll_bar.config(command=logs_text.yview)
scroll_bar.pack(side=tk.RIGHT, fill=tk.Y)
logs_text.pack(side="left")

fields = [comment_me, comment_opponent, camera, voice, token]
save_file = 'gui.bin'


def save_settings():
    outfile = open(save_file, 'wb')
    pickle.dump([field.get() for field in fields], outfile)
    outfile.close()


def load_settings():
    if os.path.exists(save_file):
        infile = open(save_file, 'rb')
        variables = pickle.load(infile)
        infile.close()
        token.set(variables[-1])
        if variables[-2] in VOICE_OPTIONS:
            voice.set(variables[-2])

        if variables[-3] in OPTIONS:
            camera.set(variables[-3])

        for i in range(2):
            fields[i].set(variables[i])


load_settings()
window.protocol("WM_DELETE_WINDOW", on_closing)
window.mainloop()
