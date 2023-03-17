#!/usr/bin/env python
# SPDX-FileCopyrightText: 2001 Jeff Epler
# SPDX-FileCopyrightText: 2008 Jeff Epler
# SPDX-FileCopyrightText: 2023 Jeff Epler
# SPDX-License-Identifier: GPL-3.0-only

from tkinter import *
from tkinter.messagebox import *
import time, random, os, traceback, string, pickle

class Setup:
    size = 0
    w = 8
    h = 8
    nbombs = 8
    totaltime = 0
    wintime = 0
    losetime = 0
    wingames = 0
    losegames = 0
    totalgames = 0
    fastest_win = -1

class Board(Setup):
    def __init__(self):
        self.tiles = tiles = []
        self.pos2tile = {}
        covered = []
        uncovered = []
        for x in range(self.w):
            for y in range(self.h):
                uncovered.append((x,y))
        while len(covered) < self.w*self.h:
            x, y = random.choice(uncovered)
            tile = Tile(x, y, random.randint(1, 2))
            for coord in tile.shape():
                if coord in covered: tile = Tile(x,y,0)
            for coord in tile.shape():
                uncovered.remove(coord)
                covered.append(coord)
            tiles.append(tile)

        for t in tiles:
                for pos in t.shape():
                        self.pos2tile[pos] = t

        nobombs = tiles[:]
        self.bombs = bombs = []
        for i in range(self.nbombs):
            x = random.choice(nobombs)
            bombs.append(x)
            nobombs.remove(x)
            x.bomb = 1
        
        for i in bombs:
            for j in self.neighbors(i):
                j.neighbor_bombs = j.neighbor_bombs + 1

    def neighbors(self, tile):
        ret = []
        for pos in tile.neighbors():
            tile = self.pos2tile[pos]
            if not tile in ret: ret.append(tile)
        return ret

    def Print(self):
        for y in range(self.h):
            for x in range(self.w):
                k = self.pos2tile[x,y]
                if k.x == x and k.y == y:
                    if k.bomb: print(end="*")
                    else: print(end=k.neighbor_bombs)
                elif k.x + k.dx[k.d] == x and k.y + k.dy[k.d] == y:
                    if k.d == 1: print(end="<")
                    else: print(end="^")
            print()

class Tile(Setup):
    dx = [0, 1, 0]
    dy = [0, 0, 1]
    dname = ["square", "horizontal", "vertical"]

    def __init__(self, x, y, d):
        self.x = x
        self.y = y
        self.d = d
        self.bomb = 0
        self.neighbor_bombs = 0
        self.revealed = 0
        self.flag = 0

    def __repr__(self): return "<Tile:%d,%d %s>" % (self.x, self.y, self.dname[self.d])

    def covers(self, x, y):
        if self.x == x and self.y == y: return 1
        x1 = self.x + self.dx[self.d]
        y1 = self.x + self.dy[self.d]
        if x1 == x and y1 == y: return 1
        return 0

    def shape(self):
        if self.d == 0: return [(self.x, self.y)]
        x1 = self.x + self.dx[self.d]
        y1 = self.y + self.dy[self.d]
        if x1 < 0 or x1 >= self.w or y1 < 0 or y1 >= self.h:
            self.d = 0
            return [(self.x, self.y)]
        return [(self.x, self.y), (x1,y1)]

    def neighbors(self):
        ret = []
        x, y = self.x, self.y
        x1 = self.x + self.dx[self.d]
        y1 = self.y + self.dy[self.d]
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                x2 = x + dx
                y2 = y + dy
                if not (x2 < 0 or x2 >= self.w or
                        y2 < 0 or y2 >= self.h or
                        (x2,y2) in ret or 
                        (x2 == x and y2 == y) or 
                        (x2 == x1 and y2 == y1)):
                    ret.append((x2,y2))

                x2 = x1 + dx
                y2 = y1 + dy
                if not ( x2 < 0 or x2 >= self.w or
                        y2 < 0 or y2 >= self.h or
                        (x2,y2) in ret or 
                        (x2 == x and y2 == y) or 
                        (x2 == x1 and y2 == y1)):
                    ret.append((x2,y2))
        ret.sort()
        return ret


# vim:ts=8:sw=4:sts=4
class Tkboard:
    def button_clicked(self, tile):
        if self.has_flag(tile): return
        self.reveal(tile)
        
    def button1(self, event):
        tile = self.w2t[event.widget]
        if self.has_flag(tile): return
        self.reveal(tile)

    colors = ['black', 'blue', 'green', 'red', 'darkblue', 'darkgreen',
                'darkred', 'orange', 'cyan', 'magenta']

    def reveal(self, tile, nolose=0):
        if tile.revealed: return
        tile.revealed = 1
        if self.num_revealed == 0:
            self.start = time.time()
            self.periodic()
        self.num_revealed = self.num_revealed + 1
        widget = self.t2w[tile]

        if tile.bomb:
            if not nolose:
                self.lost = 1
                self.done = 1
                self.status.configure(text = "You lose.")
                secs = time.time() - self.start
                Setup.totaltime = Setup.totaltime + secs
                Setup.losetime = Setup.losetime + secs
                Setup.losegames = Setup.losegames + 1
                self.game.dostats()
                widget.configure(background="red",
                                relief="groove",
                                activebackground="red")
                for t in self.board.tiles: self.reveal(t, 1)
            if not self.has_flag(tile):
                widget.configure(text="*")
            return

        if self.num_revealed == len(self.board.tiles) - len(self.board.bombs):
            if not self.lost:
                for t in self.board.tiles: self.reveal(t, 1)
                self.done = 1
                self.status.configure(text = "You win!")
                secs = time.time() - self.start
                Setup.totaltime = Setup.totaltime + secs
                Setup.wintime = Setup.wintime + secs
                Setup.wingames = Setup.wingames + 1
                if Setup.fastest_win == -1 or Setup.fastest_win > secs:
                    Setup.fastest_win = secs
                self.game.dostats()


        if self.has_flag(tile):
            widget.configure(text="!", relief="sunken", foreground="white",
                            background="black")
        elif tile.neighbor_bombs == 0:
            for t in self.neighbors(tile):
                if self.has_flag(t): continue
                self.reveal(t)
            widget.configure(text="", relief="sunken")
        else:
            widget.configure(text=str(tile.neighbor_bombs), relief="sunken",
                            foreground = self.colors[tile.neighbor_bombs],
                            activeforeground = self.colors[tile.neighbor_bombs])

    def has_flag(self, tile):
        return self.t2w[tile].cget("text") == "F"

    def neighbors(self, tile): return self.board.neighbors(tile)

    def button2press(self, event):
        tile = self.w2t[event.widget]
        for t in self.neighbors(tile):
            w = self.t2w[t]
            if not t.revealed:
                w.configure(relief="sunken")
        self.smartmiddle(tile)

    def smartmiddle(self, tile):
        flagcount = 0
        unrevealed = 0
        for t in self.neighbors(tile):
            w = self.t2w[t]
            if not t.revealed: unrevealed = unrevealed + 1
            if self.has_flag(t): flagcount = flagcount + 1
        if unrevealed == tile.neighbor_bombs:
            for t in self.neighbors(tile):
                if self.has_flag(t): continue
                if t.revealed: continue
                self.flag(t)
        if tile.revealed and flagcount == tile.neighbor_bombs:
            for t in self.neighbors(tile):
                if self.has_flag(t): continue
                if t.revealed: continue
                self.reveal(t)
                self.smartmiddle(t)

    def flag(self, tile):
        assert not tile.revealed
        self.numflags = self.numflags + 1
        self.t2w[tile].configure(text="F")
        self.update_status()

    def unflag(self, tile):
        assert not tile.revealed
        self.numflags = self.numflags - 1
        self.t2w[tile].configure(text="")
        self.update_status()

    def toggle_flag(self, tile):
        if self.has_flag(tile): self.unflag(tile)
        else: self.flag(tile)

    def button2release(self, event):
        tile = self.w2t[event.widget]
        for t in self.neighbors(tile):
            if not t.revealed:
                self.t2w[t].configure(relief="raised")

    def button3(self, event):
        tile = self.w2t[event.widget]
        if tile.revealed: return
        self.toggle_flag(tile)

    def destroy(self):
        for w in self.w2t.keys(): w.destroy()
        self.done = 1

    def update_timer(self, event = None):
        seconds = int(time.time() - self.start)
        s = seconds % 60
        m = (seconds // 60) % 60
        h = seconds // 3600
        self.timer.configure(text = "%2d:%02d:%02d" % (h,m,s))

    def update_status(self):
        self.status.configure(text = "%d/%d" %
                            (self.numflags, self.board.nbombs))

    def periodic(self, event = None):
        if self.done: return
        self.update_timer()
        self.timer.after(1000, self.periodic)

    def __init__(self, f, t, s, game):
        self.num_revealed = self.lost = self.done = 0
        self.w2t = {}
        self.t2w = {}
        self.timer = t
        self.status = s
        self.game = game
#       f.bind_class("Tile", "<Button-1>", self.button1)
        f.bind_class("Tile", "<ButtonPress-2>", self.button2press)
        f.bind_class("Tile", "<ButtonRelease-2>", self.button2release)
        f.bind_class("Tile", "<Button-3>", self.button3)
        self.board = Board()
        for tile in self.board.tiles:
            if tile.bomb: text = "*"
            elif tile.neighbor_bombs: text = str(tile.neighbor_bombs)
            else: text=""
            b = Button(f, text="", width=1,
                command=lambda s=self, t=tile: s.button_clicked(t))
            self.w2t[b] = tile
            self.t2w[tile] = b
            b.grid(column = tile.x, row = tile.y,
                columnspan = 1 + tile.dx[tile.d],
                rowspan = 1 + tile.dy[tile.d], sticky="nsew")
            b.bindtags(('Tile',) + b.bindtags())
#       self.start = time.time()
#       self.periodic()
        self.numflags = 0
        self.update_status()


class Game:
    """DominoSweeper  by Jeff Epler <jepler@unpy.net>

This game is patterned after the popular MineSweeper game and implementations
such as GnoMines.  In DominoSweeper, some of the tiles are domino-shaped,
rather than being identical squares.
"""

    def settings_window(self, event = None):
        t = Toplevel(self.t)
        f = Frame(t)

        g = Frame(f)
        b = Button(g, text="OK", command=self.prefs_command_ok)
        b.pack(side=LEFT)
        b = Button(g, text="Cancel", command=self.prefs_command_cancel)
        b.pack(side=RIGHT)
        g.pack(side=BOTTOM)

        g = Frame(f)
        Size = IntVar(t)
        Width = IntVar(t)
        Height = IntVar(t)
        Mines = IntVar(t)
        Size.set(Setup.size)
        Width.set(Setup.w)
        Height.set(Setup.h)
        Mines.set(Setup.nbombs)
        Status = self.Status = IntVar(t)
        b = Radiobutton(g, text="Tiny", variable=Size, value=0, justify=LEFT)
        b.grid(row=0, column=0, sticky=W)
        b = Radiobutton(g, text="Medium", variable=Size, value=1, justify=LEFT)
        b.grid(row=1, column=0, sticky=W)
        b = Radiobutton(g, text="Big", variable=Size, value=2, justify=LEFT)
        b.grid(row=2, column=0, sticky=W)
        b = Radiobutton(g, text="Custom", variable=Size, value=3, justify=LEFT)
        b.grid(row=3, column=0, sticky=W)
        g.pack(side=LEFT, expand=Y, fill=Y)
        g = Frame(f)
        l = Label(g, text="Width", justify=RIGHT)
        l.grid(row=0, column=0)
        e = Entry(g, textvariable=Width, justify=RIGHT, width=3)
        e.grid(row=0, column=1)
        l = Label(g, text="Height")
        l.grid(row=1, column=0)
        e = Entry(g, textvariable=Height, justify=RIGHT, width=3)
        e.grid(row=1, column=1)
        l = Label(g, text="Number of mines", justify=RIGHT)
        l.grid(row=2, column=0)
        e = Entry(g, textvariable=Mines, justify=RIGHT, width=3)
        e.grid(row=2, column=1)
        g.pack(side=RIGHT, expand=Y, fill=Y)
        f.pack()
        t.wm_protocol("WM_DELETE_WINDOW", self.prefs_command_cancel)
        t.wait_variable(Status)
        t.destroy()
        if not Status.get(): return
        Setup.size = Size.get()
        Setup.h = Height.get()
        Setup.w = Width.get()
        Setup.nbombs = Mines.get()
        pickle.dump(Setup.__dict__, open( self.rcfile(), "w"))

    def prefs_command_ok(self): self.Status.set(1)
    def prefs_command_cancel(self): self.Status.set(0)

    def rcfile(self):
        return os.path.join(os.environ['HOME'], ".dsrc")
    def readrc(self):
        try:
            if os.path.exists(self.rcfile()):
                Setup.__dict__ = pickle.load(open(self.rcfile()))
        except:
            t, v, tb = sys.exc_info()
            showerror(title="Error reading preferences",
                message=string.join(traceback.format_exception(t,v,tb), "\n"))
        
    def newgame(self, event = None):
        self.b.destroy()
        self.b = Tkboard(self.f, self.timer, self.status, self)

    def quit(self, event = None):
        self.t.destroy()

    def about(self):
        showinfo(title="About DominoSweeper",
            message=self.__doc__)

    def stats_destroy(self):
        self.stats_toplevel.destroy()
        self.stats_text = None

    def stats_window(self):
        if self.stats_text:
            self.stats_toplevel.tkraise()
            return
        t = Toplevel(self.t)
        t.wm_protocol("WM_DELETE_WINDOW", self.stats_destroy)
        t.wm_title("DominoSweeper Statistics")
        e = Text(t, height=5, width=32, relief="flat")
        self.stats_text = e
        self.stats_toplevel = t
        self.dostats()

    def dostats(self):
        def timefmt(x):
            if x < 60:
                return "%2.2f" % x
            h, m, s = int(x/3600), int(x/60) % 60, x%60
            return "%02d:%02d:%02d" % (h,m,s)
        e = self.stats_text
        if e is None: return
        e.delete(0.0, END)
        e.insert(END, "Total playing time: %s\n" % timefmt(Setup.totaltime))
        if Setup.wingames:
            e.insert(END, "%d wins, average time %s\n" %
                        (Setup.wingames,
                        timefmt(Setup.wintime / Setup.wingames)))
        if Setup.losegames:
            e.insert(END, "%d losses, average time %s\n" %
                        (Setup.losegames,
                        timefmt(Setup.losetime / Setup.losegames)))
        if Setup.totalgames:
            e.insert(END, "%d%% wins" %
                        (100. * Setup.wingames / Setup.losegames))
        if Setup.fastest_win != -1:
            e.insert(END, "Fastest win: %s" % timefmt(Setup.fastest_win))

        e.pack(side=TOP)

    def __init__(self):
        self.stats_text = None
        self.t = t = Tk()
        t.wm_title("DominoSweeper")
        t.bind("n", self.newgame)
        t.bind("q", self.quit)
        m = Menu(t)
        f = Menu(m)
        f.add_command(label="New Game", command=self.newgame,
                    underline=0, accelerator="n")
        f.add_command(label="Preferences", command=self.settings_window,
                    underline=0)
        f.add_command(label="Stats", command=self.stats_window,
                    underline=0)
        f.add_command(label="Quit", command=self.quit,
                    underline=0, accelerator="q")
        m.add_cascade(label="File", menu=f, underline=0)
        f = Menu(m)
        f.add_command(label="About", command=self.about,
                    underline=0)
        m.add_cascade(label="Help", menu=f, underline=0)
        t.configure(menu=m)

        self.f = f = Frame(t)
        f.pack(side = TOP)

        self.timer = timer = Label(t)
        self.status = status = Label(t)
        timer.pack(side = LEFT)
        status.pack(side = RIGHT)
        
        
        self.readrc()

        self.b = Tkboard(f, timer, status, self)
        mainloop()
        pickle.dump(Setup.__dict__, open(self.rcfile(), "w"))

if __name__ == '__main__': Game()

# vim:sw=4:sts=4:
