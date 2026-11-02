import logging
import os
import tkinter as tk
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from tkinter import filedialog, messagebox, ttk

import converters


PROJECT_ROOT = Path(__file__).resolve().parent.parent

results = Queue()
busy = False


def choose_input_file():
    selected = filedialog.askopenfilename(
        parent=window,
        title="Wybierz plik do konwersji",
    )

    if not selected:
        return

    input_path.set(selected)
    output_path.set("")

    targets = converters.available_targets(Path(selected))
    format_box.configure(values=targets)

    if targets:
        target_format.set(targets[0])
        status.set("Wybierz format docelowy i użyj „Zapisz jako”.")
    else:
        target_format.set("")
        status.set("Brak konwertera dla wybranego typu pliku.")

    update_controls()


def change_target_format(event=None):
    output_path.set("")
    status.set("Wybierz miejsce i nazwę pliku przez „Zapisz jako”.")


def choose_output_file():
    extension = target_format.get()

    if not input_path.get() or not extension:
        messagebox.showwarning(
            "Brak wyboru",
            "Najpierw wybierz plik wejściowy i format docelowy.",
            parent=window,
        )
        return

    source = Path(input_path.get())

    options = {
        "parent": window,
        "title": "Zapisz jako",
        "initialfile": f"{source.stem}{extension}",
        "defaultextension": extension,
        "filetypes": [
            (f"Pliki {extension[1:].upper()}", f"*{extension}"),
        ],
        "confirmoverwrite": False,
    }

    if output_path.get():
        options["initialdir"] = str(Path(output_path.get()).parent)

    selected = filedialog.asksaveasfilename(**options)

    if selected:
        output_path.set(selected)
        status.set("Gotowe do konwersji.")


def update_controls(*_):
    has_format = bool(input_path.get() and target_format.get())
    ready = has_format and bool(output_path.get())

    input_button.configure(
        state="disabled" if busy else "normal"
    )
    save_button.configure(
        state="normal" if not busy and has_format else "disabled"
    )
    format_box.configure(
        state="readonly" if not busy and has_format else "disabled"
    )
    convert_button.configure(
        state="normal" if not busy and ready else "disabled"
    )


def set_busy(value):
    global busy
    busy = value

    if busy:
        progress.start(10)
    else:
        progress.stop()

    update_controls()

def ask_existing_file(target: Path) -> str:
    choice = "cancel"

    dialog = tk.Toplevel(window)
    dialog.title("Plik już istnieje")
    dialog.transient(window)
    dialog.resizable(False, False)

    def finish(value):
        nonlocal choice
        choice = value
        dialog.destroy()

    frame = ttk.Frame(dialog, padding=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(
        frame,
        text=(
            f"Plik już istnieje:\n{target}\n\n"
            "Nadpisać go czy wybrać inną nazwę?"
        ),
        wraplength=500,
    ).pack(anchor="w", pady=(0, 20))

    buttons = ttk.Frame(frame)
    buttons.pack(anchor="e")

    ttk.Button(
        buttons,
        text="Nadpisz",
        command=lambda: finish("overwrite"),
    ).pack(side="left", padx=(0, 8))

    ttk.Button(
        buttons,
        text="Zmień nazwę…",
        command=lambda: finish("rename"),
    ).pack(side="left", padx=(0, 8))

    cancel_button = ttk.Button(
        buttons,
        text="Anuluj",
        command=lambda: finish("cancel"),
    )
    cancel_button.pack(side="left")

    dialog.protocol(
        "WM_DELETE_WINDOW",
        lambda: finish("cancel"),
    )
    dialog.bind(
        "<Escape>",
        lambda event: finish("cancel"),
    )

    dialog.wait_visibility()
    dialog.grab_set()
    cancel_button.focus_set()
    dialog.wait_window()

    return choice

def start_conversion():
    if busy:
        return

    try:
        if not all((
            input_path.get(),
            output_path.get(),
            target_format.get(),
        )):
            raise ValueError(
                "Wybierz plik wejściowy, format i ścieżkę zapisu."
            )

        source = converters.normalize_path(Path(input_path.get()))
        target = converters.normalize_path(Path(output_path.get()))
        extension = target_format.get()

        if extension not in converters.available_targets(source):
            raise ValueError(
                "Wybrany format nie jest dostępny dla tego pliku."
            )

        if target.suffix.lower() != extension:
            raise ValueError(
                f"Plik wynikowy musi mieć rozszerzenie {extension}. "
                "Wybierz ponownie „Zapisz jako”."
            )

        converters.validate_paths(source, target)

        while target.exists():
            choice = ask_existing_file(target)

            if choice == "cancel":
                status.set("Anulowano konwersję.")
                return

            if choice == "overwrite":
                break

            selected = filedialog.asksaveasfilename(
                parent=window,
                title="Wybierz inną nazwę",
                initialdir=str(target.parent),
                initialfile=target.name,
                defaultextension=extension,
                filetypes=[
                    (
                        f"Pliki {extension[1:].upper()}",
                        f"*{extension}",
                    ),
                ],
                confirmoverwrite=False,
            )

            if not selected:
                status.set("Anulowano konwersję.")
                return

            target = converters.normalize_path(Path(selected))
            output_path.set(str(target))

            if target.suffix.lower() != extension:
                raise ValueError(
                    f"Plik wynikowy musi mieć rozszerzenie {extension}. "
                    "Wybierz ponownie „Zapisz jako”."
                )

            converters.validate_paths(source, target)

    except Exception as error:
        logging.exception("Błąd przygotowania konwersji")
        status.set("Nie można rozpocząć konwersji.")
        messagebox.showerror(
            "Błąd",
            str(error),
            parent=window,
        )
        return

    set_busy(True)
    status.set(f"Trwa konwersja: {source.name} → {extension}")

    worker = Thread(
        target=conversion_worker,
        args=(source, target),
        daemon=False,
    )

    try:
        worker.start()
    except Exception as error:
        logging.exception("Nie udało się uruchomić wątku konwersji")
        set_busy(False)
        status.set("Nie można rozpocząć konwersji.")
        messagebox.showerror(
            "Błąd",
            str(error),
            parent=window,
        )
        return

    window.after(100, check_conversion_result)


def conversion_worker(source, target):
    pythoncom = None
    com_initialized = False

    try:
        if os.name == "nt":
            try:
                import pythoncom
            except ImportError:
                pass
            else:
                pythoncom.CoInitialize()
                com_initialized = True

        result = converters.convert(source, target)
        outcome = (True, result)

    except Exception as error:
        logging.exception(
            "Błąd konwersji: %s -> %s",
            source,
            target,
        )
        outcome = (False, str(error))

    finally:
        if com_initialized:
            try:
                pythoncom.CoUninitialize()
            except Exception:
                logging.exception("Błąd zwalniania COM")

    results.put(outcome)


def check_conversion_result():
    try:
        success, result = results.get_nowait()
    except Empty:
        window.after(100, check_conversion_result)
        return

    set_busy(False)

    if success:
        status.set(f"Utworzono plik: {result}")
        messagebox.showinfo(
            "Konwersja zakończona",
            f"Zapisano plik:\n{result}",
            parent=window,
        )
    else:
        status.set("Konwersja nie powiodła się.")
        messagebox.showerror(
            "Błąd konwersji",
            f"{result}\n\n"
            "Sprawdź plik wejściowy i wymagane zależności.\n"
            "Szczegóły zapisano w converter.log.",
            parent=window,
        )


def close_window():
    if busy:
        messagebox.showwarning(
            "Trwa konwersja",
            "Poczekaj na zakończenie konwersji "
            "przed zamknięciem aplikacji.",
            parent=window,
        )
        return

    window.destroy()


def main():
    global window
    global input_path, output_path, target_format, status
    global format_box, input_button, save_button, convert_button
    global progress

    window = tk.Tk()
    window.title("Konwerter plików")
    window.minsize(720, 320)
    window.protocol("WM_DELETE_WINDOW", close_window)

    input_path = tk.StringVar()
    output_path = tk.StringVar()
    target_format = tk.StringVar()
    status = tk.StringVar(value="Wybierz plik do konwersji.")

    frame = ttk.Frame(window, padding=20)
    frame.grid(row=0, column=0, sticky="nsew")

    window.columnconfigure(0, weight=1)
    window.rowconfigure(0, weight=1)
    frame.columnconfigure(1, weight=1)

    ttk.Label(
        frame,
        text="Plik wejściowy:",
    ).grid(
        row=0, column=0, sticky="w", padx=(0, 10), pady=8
    )

    ttk.Entry(
        frame,
        textvariable=input_path,
        state="readonly",
    ).grid(
        row=0, column=1, sticky="ew", pady=8
    )

    input_button = ttk.Button(
        frame,
        text="Wybierz plik…",
        command=choose_input_file,
    )
    input_button.grid(
        row=0, column=2, padx=(10, 0), pady=8
    )

    ttk.Label(
        frame,
        text="Format docelowy:",
    ).grid(
        row=1, column=0, sticky="w", padx=(0, 10), pady=8
    )

    format_box = ttk.Combobox(
        frame,
        textvariable=target_format,
        state="disabled",
        width=12,
    )
    format_box.grid(
        row=1, column=1, sticky="w", pady=8
    )
    format_box.bind(
        "<<ComboboxSelected>>",
        change_target_format,
    )

    ttk.Label(
        frame,
        text="Plik wynikowy:",
    ).grid(
        row=2, column=0, sticky="w", padx=(0, 10), pady=8
    )

    ttk.Entry(
        frame,
        textvariable=output_path,
        state="readonly",
    ).grid(
        row=2, column=1, sticky="ew", pady=8
    )

    save_button = ttk.Button(
        frame,
        text="Zapisz jako…",
        command=choose_output_file,
        state="disabled",
    )
    save_button.grid(
        row=2, column=2, padx=(10, 0), pady=8
    )

    convert_button = ttk.Button(
        frame,
        text="Konwertuj",
        command=start_conversion,
        state="disabled",
    )
    convert_button.grid(
        row=3, column=1, sticky="e", pady=12
    )

    progress = ttk.Progressbar(
        frame,
        mode="indeterminate",
    )
    progress.grid(
        row=4, column=0, columnspan=3, sticky="ew", pady=(0, 10)
    )

    ttk.Label(
        frame,
        textvariable=status,
        wraplength=650,
    ).grid(
        row=5, column=0, columnspan=3, sticky="w", pady=(8, 0)
    )

    for variable in (input_path, output_path, target_format):
        variable.trace_add("write", update_controls)

    update_controls()
    window.mainloop()


if __name__ == "__main__":
    logging.basicConfig(
        filename=PROJECT_ROOT / "converter.log",
        encoding="utf-8",
        level=logging.WARNING,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )
    main()
