import os
import shutil
import random
import tkinter as tk
import json
import glob
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD

locales = {}
current_locale = {}
current_lang_code = "ru"  # язык по умолчанию
input_folders = []
output_folder = ""

def load_locales():
    global locales, current_locale, current_lang_code
    locales.clear()
    for file in glob.glob("randloc-*.json"):
        lang_code = file.split("-")[-1].split(".")[0]
        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "language" in data:
                locales[lang_code] = data
    if current_lang_code in locales:
        current_locale = locales[current_lang_code]
    elif locales:
        current_lang_code, current_locale = next(iter(locales.items()))

def build_menus():
    menubar.delete(0, tk.END)  # очищаем всё

    help_menu = tk.Menu(menubar, tearoff=0)
    help_menu.add_command(
        label=current_locale.get("about_title", "О программе"),
        command=show_about
    )
    menubar.add_cascade(label=current_locale.get("menu_help", "Справка"), menu=help_menu)

    language_menu = tk.Menu(menubar, tearoff=0)
    for lang_code, lang_data in locales.items():
        language_menu.add_command(
            label=lang_data["language"],
            command=lambda code=lang_code: set_language(code)
        )
    menubar.add_cascade(label=current_locale.get("menu_language", "Язык"), menu=language_menu)

    root.config(menu=menubar)


def set_language(lang_code):
    global current_lang_code, current_locale
    if lang_code in locales:
        current_lang_code = lang_code
        current_locale = locales[lang_code]
        update_ui_texts()
        build_menus()

def drop_inside(event):
    paths = root.tk.splitlist(event.data)
    for path in paths:
        if os.path.isdir(path) and path not in input_folders:
            input_folders.append(path)
            folder_list.insert(tk.END, path)

def update_ui_texts():
    root.title(current_locale.get("title", "Рандомайзер песен"))
    drag_label.config(text=current_locale.get("drag_here", "Перетащите папки сюда:"))
    select_output_folder_btn.config(text=current_locale.get("choose_output", "Выберите выходную папку"))
    output_label.config(text=current_locale.get("output_folder", "Выходная папка") + ": " + (output_folder or current_locale.get("not_selected", "не выбрана")))
    remove_button.config(text=current_locale.get("remove_folders", "Удалить выбранные папки"))
    generate_button.config(text=current_locale.get("generate", "Сгенерировать"))

def remove_selected_folders():
    selected_indices = list(folder_list.curselection())
    for index in reversed(selected_indices):
        input_folders.pop(index)
        folder_list.delete(index)

def select_output_folder():
    global output_folder
    folder = filedialog.askdirectory(title=current_locale.get("choose_output", "Выберите выходную папку"))
    if folder:
        output_folder = folder
        output_label.config(text=f"{current_locale.get('output_folder', 'Выходная папка')}: {output_folder}")

def show_about():
    messagebox.showinfo(
        current_locale.get("about_title", "О программе"),
        current_locale.get("about_text", "Эта программа случайным образом формирует музыкальные блоки из выбранных папок.\n\n1. Перетащите в список несколько папок с треками.\n2. Программа сформирует блоки по максимальному количеству треков среди них.\n3. Из каждой папки в блок случайно выбирается трек (при нехватке — с повторами, помеченные *).\n4. Выберите папку, куда сохранить результат.\n5. Программа создаст упорядоченные треки и файл tracklist.txt.\n\nПрограмма создана dzhemvrot по идее gijelie.\n2025.")
    )

def generate_playlist():
    if not input_folders:
        messagebox.showerror("Ошибка", current_locale.get("error_input", "Не выбраны входные папки."))
        return
    if not output_folder:
        messagebox.showerror("Ошибка", current_locale.get("error_output", "Не выбрана выходная папка."))
        return

    all_tracks = {}
    max_tracks = 0

    for folder in input_folders:
        tracks = [f for f in os.listdir(folder) if f.lower().endswith(('.mp3', '.wav', '.flac', '.aac', '.ogg'))]
        all_tracks[folder] = tracks
        max_tracks = max(max_tracks, len(tracks))

    filled_tracks = {}
    repeated_flags = {}
    for folder, tracks in all_tracks.items():
        full_list = []
        flags = []
        original = list(tracks)
        while len(full_list) < max_tracks:
            random.shuffle(tracks)
            for t in tracks:
                full_list.append(t)
                flags.append(len(full_list) >= len(original))
                if len(full_list) >= max_tracks:
                    break
        filled_tracks[folder] = full_list[:max_tracks]
        repeated_flags[folder] = flags[:max_tracks]

    result_list = []
    track_counter = 1

    for i in range(max_tracks):
        for folder in input_folders:
            track = filled_tracks[folder][i]
            is_repeat = repeated_flags[folder][i]
            folder_name = os.path.basename(folder)
            src_path = os.path.join(folder, track)

            display_number = f"{track_counter}*" if is_repeat else f"{track_counter}"
            file_number = f"{track_counter:02d}"
            dst_name = f"{file_number}. {folder_name} - {track}"
            dst_path = os.path.join(output_folder, dst_name)

            shutil.copy2(src_path, dst_path)
            result_list.append(f"{display_number}. {folder_name} - {track}")
            track_counter += 1
        result_list.append("")

    tracklist_path = os.path.join(output_folder, "tracklist.txt")
    with open(tracklist_path, "w", encoding="utf-8") as f:
        for line in result_list:
            f.write(line + "\n")

    messagebox.showinfo(
        current_locale.get("success_title", "Успешно"),
        current_locale.get("success", "Список из {count} треков создан!\nФайл tracklist.txt записан.").format(count=track_counter - 1)
    )

# === Интерфейс ===
root = TkinterDnD.Tk()
root.title("Рандомайзер песен")
root.geometry("700x500")

# Меню
menubar = tk.Menu(root)
load_locales()
build_menus()  # вместо ручного добавления меню


# Основной фрейм
frame = tk.Frame(root, padx=10, pady=10)
frame.pack(fill=tk.BOTH, expand=True)

drag_label = tk.Label(frame, text="Перетащите папки сюда:")
drag_label.pack()

folder_list = tk.Listbox(frame, selectmode=tk.MULTIPLE, width=80, height=15)
folder_list.pack(fill=tk.BOTH, expand=True, pady=5)
folder_list.drop_target_register(DND_FILES)
folder_list.dnd_bind('<<Drop>>', drop_inside)

button_frame = tk.Frame(frame)
button_frame.pack(pady=5)

remove_button = tk.Button(button_frame, text="Удалить выбранные папки", command=remove_selected_folders)
remove_button.pack(side=tk.LEFT, padx=5)

select_output_folder_btn = tk.Button(frame, text="Выбрать выходную папку", command=select_output_folder)
select_output_folder_btn.pack(pady=5)

output_label = tk.Label(frame, text="Выходная папка: не выбрана")
output_label.pack()

generate_button = tk.Button(frame, text="Сгенерировать", command=generate_playlist, bg="green", fg="white")
generate_button.pack(pady=10)

update_ui_texts()
root.mainloop()
