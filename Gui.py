import math
import tkinter as tk
from threading import Thread
from tkinter import filedialog, messagebox, ttk
from typing import TypedDict

from PIL import Image, ImageGrab
from PIL.ImageTk import PhotoImage
from ttkthemes import ThemedTk

from Board import Board
from Card import Card, CardBitmap
from Game import Game
from Rank import Rank
from Stack import Stack

type Bbox = tuple[int, int, int, int]  # (left, top, right, bottom)


def gui_prepare():
    import platform
    from ctypes import windll

    if platform.system() != "Windows":
        raise NotImplementedError("Only support windows")
    try:
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        print("Warn: Cannot set dpi awareness")


class Screenshot:
    image: Image.Image | None = None
    bbox: Bbox = (0, 0, 1920, 1080)

    @classmethod
    def capture_window(cls, name: str):
        """capture screenshot by window's title"""
        name = name.strip()
        if not name:
            messagebox.showerror(
                "Error",
                "Please input window title. Default game window is: "
                + Gui.DEFAULT_WINDOW_TITLE,
            )
            return False

        hwnd, bbox = cls.get_window_by_name(name)
        if hwnd == 0:
            messagebox.showerror("Error", f'No visible window named "{name}" is found!')
            return False

        cls.image = ImageGrab.grab(all_screens=True, window=hwnd)  # whole window
        if bbox[3] - bbox[1] > cls.image.height:
            # with title bar
            cls.bbox = (bbox[0], bbox[3] - cls.image.height, bbox[2], bbox[3])
        else:
            cls.bbox = bbox  # frameless
        return True

    @classmethod
    def select_image(cls):
        """use image file as screenshot"""
        file = filedialog.askopenfilename(
            title="Select a screenshot",
            filetypes=[("Image", "*.png;*.jpg;*.jpeg"), ("All", "*.*")],
            initialdir="./ex",
        )
        if not file:
            return False  # cancel
        cls.image = Image.open(file)
        cls.bbox = (0, 0, cls.image.width, cls.image.height)
        return True

    @classmethod
    def scale(cls):
        if cls.image is None:
            return (1.0, 1.0)
        return (cls.image.width / 1920, cls.image.height / 1080)

    @classmethod
    def transform(
        cls, *, crop: Bbox | None = None, resize: tuple[int, int] | None = None
    ):
        if cls.image is None:
            return Image.new("RGB", (1, 1))
        img = cls.image
        if crop is not None:
            img = img.crop(crop)
        if resize is not None and (resize[0] != img.width or resize[1] != img.height):
            img = img.resize(resize, Image.Resampling.LANCZOS)
        return img

    @staticmethod
    def get_window_by_name(name: str) -> tuple[int, Bbox]:
        """Get window id and bbox of given window name"""
        from ctypes import byref, windll
        from ctypes.wintypes import RECT

        hwnd = windll.user32.FindWindowW(0, name)
        if hwnd == 0:
            print(hwnd, "<nil>")
            return 0, (0, 0, 0, 0)
        rect = RECT()
        windll.user32.GetWindowRect(hwnd, byref(rect))
        bbox = (rect.left, rect.top, rect.right, rect.bottom)
        print(hwnd, rect, bbox)
        return hwnd, bbox


class Gui:
    DEFAULT_WINDOW_TITLE = "EXAPUNKS"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("EXAPUNKS Automation")
        self.root.geometry("1000x700")

        self.window_name = tk.StringVar(value=self.DEFAULT_WINDOW_TITLE)
        self.tk_image = None  # tkinter image
        self.board = Board()
        self.board_n = tk.IntVar(value=1)

        self.desk_left = tk.IntVar(value=366)
        self.desk_top = tk.IntVar(value=460)
        self.desk_right = tk.IntVar(value=1556)
        self.desk_bottom = tk.IntVar(value=730)

        self.card_ranks = tk.IntVar(value=9)
        self.card_width = tk.IntVar(value=120)
        self.card_height = tk.IntVar(value=180)

        self.hand_x = tk.IntVar(value=1430)
        self.hand_y = tk.IntVar(value=280)

        self.newgame_x = tk.IntVar(value=1400)
        self.newgame_y = tk.IntVar(value=900)

        self.offset_x = tk.IntVar(value=5)
        self.offset_y = tk.IntVar(value=4)
        self.ocr_n = tk.IntVar(value=14)

        self.solve_text = tk.StringVar()
        self.info_text = tk.StringVar()

        self.ocr_x = tk.IntVar(value=0)
        self.ocr_y = tk.IntVar(value=0)
        self.ocr_tk_images: list[PhotoImage] = []

        sections = ttk.Notebook(root)

        # 1. capture/solve
        capture_frame = ttk.Frame(sections, padding="10")
        capture_frame.pack(fill=tk.X, anchor=tk.N)
        ttk.Label(capture_frame, text="Window Title:").grid(
            row=0, column=0, padx=5, pady=5
        )
        ttk.Entry(capture_frame, textvariable=self.window_name, width=30).grid(
            row=0, column=1, padx=5, pady=5
        )
        ttk.Button(capture_frame, text="Capture", command=self.capture_window).grid(
            row=0, column=2, padx=5, pady=5
        )
        ttk.Button(capture_frame, text="File...", command=self.select_image_file).grid(
            row=0, column=3, padx=5, pady=5
        )

        ttk.Label(capture_frame, text="Rounds:").grid(row=1, column=0, padx=5, pady=5)
        ttk.Spinbox(
            capture_frame, textvariable=self.board_n, from_=1, to=999, increment=1
        ).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(capture_frame, text="Solve", command=self.solve_games).grid(
            row=1, column=2, padx=5, pady=5
        )
        ttk.Button(capture_frame, text="Quick", command=self.solve_games_quick).grid(
            row=1, column=3, padx=5, pady=5
        )
        ttk.Button(capture_frame, text="Stop", command=self.press_solve_stop).grid(
            row=1, column=4, padx=5, pady=5
        )

        self.solve_prog = ttk.Progressbar(capture_frame, length=200, value=0, maximum=1)
        self.solve_prog.grid(row=2, column=0, columnspan=2, padx=5, pady=5)
        ttk.Label(capture_frame, textvariable=self.solve_text).grid(
            row=2, column=2, columnspan=3, padx=5, pady=5, sticky=tk.EW
        )

        sections.add(capture_frame, text="Window")

        sections.pack(fill=tk.BOTH, expand=True)

        # 2 regions of interest
        roi_frame = ttk.Frame(sections, padding="10")
        roi_frame.pack(fill=tk.X, anchor=tk.S)

        DICT_SBX = TypedDict(
            "DICT_SBX", {"from_": float, "to": float, "increment": float, "width": int}
        )
        spinbox_opts: DICT_SBX = {"from_": 0, "to": 1e6, "increment": 1, "width": 8}

        DICT_GRID = TypedDict(
            "DICT_GRID",
            {"row": int, "column": int, "padx": float | str, "pady": float | str},
        )
        grid_opts: DICT_GRID = {"row": 0, "column": 0, "padx": 2, "pady": 5}

        ttk.Label(roi_frame, text="Main Card Region:").grid(
            columnspan=2, sticky=tk.EW, **grid_opts
        )
        grid_opts["column"] += 2
        ttk.Spinbox(roi_frame, textvariable=self.desk_left, **spinbox_opts).grid(
            **grid_opts
        )
        grid_opts["column"] += 1
        ttk.Spinbox(roi_frame, textvariable=self.desk_top, **spinbox_opts).grid(
            **grid_opts
        )
        grid_opts["column"] += 1
        ttk.Spinbox(roi_frame, textvariable=self.desk_right, **spinbox_opts).grid(
            **grid_opts
        )
        grid_opts["column"] += 1
        ttk.Spinbox(roi_frame, textvariable=self.desk_bottom, **spinbox_opts).grid(
            **grid_opts
        )
        grid_opts["column"] += 1
        ttk.Label(roi_frame, text="Ranks:").grid(sticky=tk.EW, **grid_opts)
        grid_opts["column"] += 1
        ttk.Spinbox(roi_frame, textvariable=self.card_ranks, **spinbox_opts).grid(
            **grid_opts
        )

        grid_opts["row"] += 1
        grid_opts["column"] = 0
        ttk.Label(roi_frame, text="Shift Card Center:").grid(
            columnspan=2, sticky=tk.EW, **grid_opts
        )
        grid_opts["column"] += 2
        ttk.Spinbox(roi_frame, textvariable=self.hand_x, **spinbox_opts).grid(
            **grid_opts
        )
        grid_opts["column"] += 1
        ttk.Spinbox(roi_frame, textvariable=self.hand_y, **spinbox_opts).grid(
            **grid_opts
        )
        grid_opts["column"] += 1
        ttk.Label(roi_frame, text="Card size:").grid(sticky=tk.EW, **grid_opts)
        grid_opts["column"] += 1
        ttk.Spinbox(roi_frame, textvariable=self.card_width, **spinbox_opts).grid(
            **grid_opts
        )
        grid_opts["column"] += 1
        ttk.Spinbox(roi_frame, textvariable=self.card_height, **spinbox_opts).grid(
            **grid_opts
        )

        grid_opts["row"] += 1
        grid_opts["column"] = 0
        ttk.Label(roi_frame, text="New Game:").grid(
            columnspan=2, sticky=tk.EW, **grid_opts
        )
        grid_opts["column"] += 2
        ttk.Spinbox(roi_frame, textvariable=self.newgame_x, **spinbox_opts).grid(
            **grid_opts
        )
        grid_opts["column"] += 1
        ttk.Spinbox(roi_frame, textvariable=self.newgame_y, **spinbox_opts).grid(
            **grid_opts
        )
        grid_opts["column"] += 1
        ttk.Label(roi_frame, text="OCR offset:").grid(sticky=tk.EW, **grid_opts)
        grid_opts["column"] += 1
        ttk.Spinbox(roi_frame, textvariable=self.offset_x, **spinbox_opts).grid(
            **grid_opts
        )
        grid_opts["column"] += 1
        ttk.Spinbox(roi_frame, textvariable=self.offset_y, **spinbox_opts).grid(
            **grid_opts
        )
        grid_opts["column"] += 1
        ttk.Label(roi_frame, text="OCR size:").grid(sticky=tk.EW, **grid_opts)
        grid_opts["column"] += 1
        ttk.Spinbox(
            roi_frame, textvariable=self.ocr_n, from_=12, to=20, increment=1, width=8
        ).grid(**grid_opts)

        grid_opts["row"] += 1
        grid_opts["column"] = 0
        ttk.Button(roi_frame, text="Refresh", command=self.redraw_canvas).grid(
            **grid_opts
        )
        grid_opts["column"] += 1
        ttk.Label(roi_frame, textvariable=self.info_text).grid(
            columnspan=5, sticky=tk.EW, **grid_opts
        )

        sections.add(roi_frame, text="Region")

        # 3. ocr
        ocr_frame = ttk.Frame(sections, padding="10")
        ocr_frame.pack(fill=tk.X, anchor=tk.S)

        spinbox_opts = {"from_": 0, "to": 10, "increment": 1, "width": 8}
        grid_opts = {"row": 0, "column": 0, "padx": 2, "pady": 5}

        ttk.Label(ocr_frame, text="Card:").grid(**grid_opts)
        grid_opts["column"] += 1
        ttk.Spinbox(ocr_frame, textvariable=self.ocr_x, **spinbox_opts).grid(
            **grid_opts
        )
        grid_opts["column"] += 1
        ttk.Spinbox(ocr_frame, textvariable=self.ocr_y, **spinbox_opts).grid(
            **grid_opts
        )

        grid_opts["row"] += 1
        grid_opts["column"] = 0
        ttk.Button(ocr_frame, text="Refresh", command=self.redraw_canvas).grid(
            **grid_opts
        )

        grid_opts["row"] += 1
        grid_opts["column"] = 0
        self.ocr_canvas = tk.Canvas(ocr_frame, width=800, height=100)
        self.ocr_canvas.grid(columnspan=8, sticky=tk.EW, **grid_opts)

        sections.add(ocr_frame, text="OCR")

        # 4. preview layout, canvas (16:9)
        preview_frame = ttk.Frame(root, padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(preview_frame, bg="gray", width=800, height=450)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.solve_stop = False  # stop botton pressed
        self.solve_th: Thread | None = None  # game solve thread

    def capture_window(self):
        """Capture window and render on canvas"""
        try:
            if Screenshot.capture_window(self.window_name.get()):
                self.detect_cards()
                self.render_canvas()
        except Exception as e:
            messagebox.showerror("Screenshot Failed", f"Error: {e}")
            raise e

    def select_image_file(self):
        """Select image file and render on canvas"""
        try:
            if Screenshot.select_image():
                self.detect_cards()
                self.render_canvas()
        except Exception as e:
            messagebox.showerror("Open File Failed", f"Error: {e}")
            raise e

    def redraw_canvas(self):
        try:
            self.render_canvas()
        except Exception as e:
            messagebox.showerror("Draw Error", f"Error: {e}")
            raise e

    def get_fitted_size(self, wh: tuple[int, int]):
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        scale = min(canvas_w / wh[0], canvas_h / wh[1], 1)
        return (int(wh[0] * scale), int(wh[1] * scale))

    def render_canvas(self):
        # clear canvas
        self.canvas.delete("all")
        self.ocr_canvas.delete("all")
        self.ocr_tk_images = []
        info = "(Resized to 1920x1080)"
        if Screenshot.image is None:
            self.info_text.set(info)
            return
        # keep w/h ratio and fit to canvas
        new_size = self.get_fitted_size(Screenshot.image.size)
        print(f"screen {Screenshot.image.size} -> {new_size}")
        image_w, image_h = new_size
        scale_w, scale_h = image_w / 1920, image_h / 1080
        self.tk_image = PhotoImage(Screenshot.transform(resize=new_size))
        # render canvas
        self.canvas.config(scrollregion=(0, 0, image_w, image_h))
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.canvas.create_rectangle(
            int(self.desk_left.get()) * scale_w,
            int(self.desk_top.get()) * scale_h,
            int(self.desk_right.get()) * scale_w,
            int(self.desk_bottom.get()) * scale_h,
            outline="blue",
            width=1,
            fill="blue",
            stipple="gray12",
        )
        self.canvas.create_oval(
            (int(self.hand_x.get()) - 10) * scale_w,
            (int(self.hand_y.get()) - 10) * scale_h,
            (int(self.hand_x.get()) + 10) * scale_w,
            (int(self.hand_y.get()) + 10) * scale_h,
            outline="purple",
            width=1.5,
        )
        self.canvas.create_oval(
            (int(self.newgame_x.get()) - 10) * scale_w,
            (int(self.newgame_y.get()) - 10) * scale_h,
            (int(self.newgame_x.get()) + 10) * scale_w,
            (int(self.newgame_y.get()) + 10) * scale_h,
            outline="aqua",
            width=1.5,
        )
        if False:  # debug: print grid
            gridx = 200
            for x in range(gridx, 1920, gridx):
                canvas_x = x * scale_w
                self.canvas.create_line(
                    canvas_x, 0, canvas_x, image_h, width=1, fill="green"
                )
            gridy = 200
            for y in range(gridy, 1080, gridy):
                canvas_y = y * scale_h
                self.canvas.create_line(
                    0, canvas_y, image_w, canvas_y, width=1, fill="green"
                )
        # show ocr part
        c = self.card_bbox(self.ocr_x.get(), self.ocr_y.get())
        c1 = self.bbox_scale(c, (scale_w, scale_h))
        self.canvas.create_rectangle(
            c1[0],
            c1[1],
            c1[2],
            c1[3],
            outline="red",
            width=1,
            fill="red",
            stipple="gray25",
        )
        print("ocr rect", c1, "scale", (scale_w, scale_h))
        c2 = self.bbox_scale(c, Screenshot.scale())
        n = int(self.ocr_n.get())
        ocr_img = Screenshot.transform(crop=c2, resize=(n, n))
        print("ocr image", c, "size", ocr_img.size)

        info = (
            f"image(w={Screenshot.image.width},h={Screenshot.image.height}) "
            + f"margin(x={self.card_marginx()},y={self.card_marginy()}) "
            + f"ocr(x={c[0]},y={c[1]}) {info}"
        )
        self.info_text.set(info)

        # ocr result canvas
        if self.ocr_result is not None:
            for rank in range(len(self.ocr_result)):
                x = rank * 30 + 10
                for row in range(len(self.ocr_result[rank])):
                    y = row * 20 + 10
                    r = self.ocr_result[rank][row]
                    self.ocr_canvas.create_text(
                        x, y, text=r[1], fill="red" if r[0] else "black"
                    )
        else:
            self.ocr_canvas.create_text(30, 10, text="Recognition failed")

        img_tk = PhotoImage(ocr_img)
        self.ocr_tk_images.append(img_tk)
        self.ocr_canvas.create_image(360, 10, image=img_tk)
        blue: list[int] = ocr_img.get_flattened_data(2)  # pyright: ignore[reportAssignmentType]
        face, diffs = CardBitmap.compare(blue, n)
        self.ocr_canvas.create_text(360, 30, text=f"={CardBitmap.NAMES[face]}")
        for i in range(len(diffs)):
            x = i * 40 + 400
            img_tk = PhotoImage(
                Image.frombytes(
                    "L", (12, 12), CardBitmap.to_bytes(CardBitmap.CARDS[i]), "raw"
                )
            )
            self.ocr_tk_images.append(img_tk)
            self.ocr_canvas.create_image(x, 10, image=img_tk)
            self.ocr_canvas.create_text(x, 30, text=f"{diffs[i]:.1f}")

    def card_marginx(self):
        cw = int(self.card_width.get())
        dw = int(self.desk_right.get()) - int(self.desk_left.get())
        dn = int(self.card_ranks.get())
        return (dw - cw) / (dn - 1) - cw

    def card_marginy(self):
        ch = int(self.card_height.get())
        dh = int(self.desk_bottom.get()) - int(self.desk_top.get())
        dn = math.ceil(36 / int(self.card_ranks.get()))  # 36 cards
        return (dh - ch) / (dn - 1)

    def card_bbox(self, x: int, y: int) -> Bbox:
        """resolution is (1920, 1080)"""
        left = round(
            x * (self.card_width.get() + self.card_marginx())
            + self.desk_left.get()
            + self.offset_x.get()
        )
        top = round(y * self.card_marginy() + self.desk_top.get() + self.offset_y.get())
        n = int(self.ocr_n.get())
        return (left, top, left + n, top + n)

    @staticmethod
    def bbox_scale(bbox: Bbox, scale: tuple[float, float]) -> Bbox:
        """(l,t,r,b) x (w,h) -> (l*w,t*h,r*w,b*h)"""
        return (
            int(bbox[0] * scale[0]),
            int(bbox[1] * scale[1]),
            int(bbox[2] * scale[0]),
            int(bbox[3] * scale[1]),
        )

    def detect_cards(self):
        if Screenshot.image is None:
            return []
        ranks = int(self.card_ranks.get())
        dn = math.ceil(36 / ranks)  # 36 cards
        n = int(self.ocr_n.get())  # n*n pixels
        scale = Screenshot.scale()
        result = []
        for x in range(ranks):
            stack: list[tuple[bool, str]] = []
            for y in range(dn):
                c2 = self.bbox_scale(self.card_bbox(x, y), scale)
                img = Screenshot.transform(crop=c2, resize=(n, n))
                red: list[int] = img.get_flattened_data(0)  # pyright: ignore[reportAssignmentType]
                red_avg = sum(red) / len(red)
                is_red = red_avg > 200
                blue: list[int] = img.get_flattened_data(2)  # pyright: ignore[reportAssignmentType]
                face, diffs = CardBitmap.compare(blue, n)
                name = CardBitmap.NAMES[face]
                print(
                    f"card({x},{y}) red={red_avg:.2f}->{is_red} "
                    + f"gray={sum(blue) / len(blue):.2f}->{name} {diffs}"
                )
                stack.append((is_red, name))
            result.append(stack)
        self.ocr_result: list[list[tuple[bool, str]]] = result
        print(result)
        return result

    @staticmethod
    def to_old_card(is_red: bool, face: str):
        if face in ["6", "7", "8", "9"]:
            return Card(face, "R" if is_red else "B")
        elif face == "10":
            return Card("0", "R" if is_red else "B")
        else:
            return Card("F", face[0])

    def make_game(self):
        if Screenshot.capture_window(self.window_name.get()):
            self.detect_cards()
            self.render_canvas()
            ranks: list[Rank] = []
            for i in range(len(self.ocr_result)):
                cards: list[Card] = []
                for r in self.ocr_result[i]:
                    cards.append(self.to_old_card(*r))
                ranks.append(Rank(i, Stack.from_cards(cards)))
            return Game(ranks)
        else:
            raise Exception("Nothing captured")

    def update_board(self):
        if not Screenshot.capture_window(self.window_name.get()):
            raise Exception("Nothing captured")
        scale = Screenshot.scale()

        self.board.left_offset = Screenshot.bbox[0] + int(
            self.desk_left.get() * scale[0]
        )
        self.board.card_width = int(self.card_width.get() * scale[0])
        self.board.horizontal_spacing = int(
            (self.card_width.get() + self.card_marginx()) * scale[0]
        )

        self.board.top_offset = Screenshot.bbox[1] + int(self.desk_top.get() * scale[1])
        self.board.vertical_spacing = int(self.card_marginy() * scale[1])

        self.board.hand_x = Screenshot.bbox[0] + int(self.hand_x.get() * scale[0])
        self.board.hand_y = Screenshot.bbox[1] + int(self.hand_y.get() * scale[1])

        self.board.newgame_x = Screenshot.bbox[0] + int(self.newgame_x.get() * scale[0])
        self.board.newgame_y = Screenshot.bbox[1] + int(self.newgame_y.get() * scale[1])

        self.solve_text.set(
            f"left={self.board.left_offset} top={self.board.top_offset} "
            f"hand=({self.board.hand_x},{self.board.hand_y}) "
            + f"newgame=({self.board.newgame_x},{self.board.newgame_y}) "
        )

    def press_solve_stop(self):
        self.solve_stop = True

    def on_solve_complete(self, n):
        self.solve_prog.config(value=n)
        if self.solve_stop:
            self.solve_stop = False
            return True  # stop iteration
        return False

    @staticmethod
    def solve_game_thread(inst):
        n = int(inst.board_n.get())
        inst.solve_prog.config(value=0, maximum=n)
        inst.board.play_games(
            n,
            inst.make_game,
            inst.on_solve_complete,
        )

    def solve_games(self):
        try:
            if self.solve_th is not None:
                self.solve_th.join(30)
            self.update_board()
            self.solve_th = Thread(target=self.solve_game_thread, args=(self,))
            self.solve_th.start()
        except Exception as e:
            messagebox.showerror("Solve Error", f"Error: {e}")
            raise e

    @staticmethod
    def solve_quick_thread(inst):
        n = int(inst.board_n.get())
        inst.solve_prog.config(value=0, maximum=n)
        inst.board.play_quick_games(
            n,
            lambda: inst.make_game(),
            lambda k: inst.solve_prog.config(value=k),
        )

    def solve_games_quick(self):
        try:
            if self.solve_th is not None:
                self.solve_th.join(30)
            self.update_board()
            self.solve_th = Thread(target=self.solve_quick_thread, args=(self,))
            self.solve_th.start()
        except Exception as e:
            messagebox.showerror("Solve Error", f"Error: {e}")
            raise e


if __name__ == "__main__":
    gui_prepare()
    root = ThemedTk(theme="arc")
    app = Gui(root)
    root.mainloop()
