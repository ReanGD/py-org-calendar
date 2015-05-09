import calendar

try:
    import Tkinter
    import tkFont
except ImportError: # py3k
    import tkinter as Tkinter
    import tkinter.font as tkFont

import ttk

class CalendarConfig:
    def __init__(self):
        self.firstweekday = calendar.MONDAY
        self.select_bg = '#ecffc4'
        self.select_fg = '#05640e'
        self.header_bg = 'grey90'
    
class CalendarColumn(ttk.Treeview):
    items_cnt = 6
    def __init__(self, master):
        ttk.Treeview.__init__(self, master, height=7, selectmode='none', show='')
        self.pack(side=Tkinter.LEFT, fill=Tkinter.BOTH, expand=True)

    def config(self, name, config, width, font):
        self['columns'] = name
        self.tag_configure('header', background=config.header_bg)
        self.insert('', 'end', values=[name], tag='header')
        self.items = [self.insert('', 'end', values='') for _ in range(CalendarColumn.items_cnt)]
        self.column(name, minwidth=width, width=width, anchor='e')
        canvas = Tkinter.Canvas(self,
                                background=config.select_bg,
                                borderwidth=0,
                                highlightthickness=0)
        canvas.text = canvas.create_text(0, 0, fill=config.select_fg, anchor='w')
        self._font = font
        self._canvas = canvas
        canvas.bind('<ButtonPress-1>', lambda evt: self.remove_selection())
        self.bind('<Configure>', lambda evt: self.remove_selection())
        self.bind('<ButtonPress-1>', self._on_click)

    def remove_selection(self):
        self._canvas.place_forget()

    def _show_selection(self, text, bbox):
        x, y, width, height = bbox

        textw = self._font.measure(text)

        canvas = self._canvas
        canvas.configure(width=width, height=height)
        canvas.coords(canvas.text, width - textw, height / 2 - 1)
        canvas.itemconfigure(canvas.text, text=text)
        canvas.place(in_=self, x=x, y=y)

    def _on_click(self, evt):
        x, y = evt.x, evt.y
        item = self.identify_row(y)
        column = self.identify_column(x)

        if not column or not item in self.items:
            # clicked in the weekdays row or just outside the columns
            return

        item_values = self.item(item)['values']
        if not len(item_values): # row is empty for this month
            return

        text = item_values[int(column[1]) - 1]
        if not text: # date is empty
            return

        bbox = self.bbox(item, column)
        if not bbox: # calendar not visible yet
            return

        self.master.remove_selection()
        self._show_selection('%02d' % text, bbox)

class CalendarMonth(ttk.Treeview):
    def __init__(self, master):
        ttk.Treeview.__init__(self, show='', selectmode='none', height=7)
        self._cols = [CalendarColumn(self) for _ in range(7)]
        self.pack(in_=master, expand=1, fill='both', side='bottom')

    def config(self, cols, font, config):
        maxwidth = max(font.measure(col) for col in cols)
        for i, col in enumerate(self._cols):
            col.config(cols[i], config, maxwidth, font)

    def build(self, weeks):
        for iweek in range(CalendarColumn.items_cnt):
            week = weeks[iweek] if iweek < len(weeks) else [0] * 7
            fmt_week = [('%02d' % day) if day > 0 else '' for day in week]
            for icol, col in enumerate(self._cols):
                col.item(col.items[iweek], values=fmt_week[icol])

    def remove_selection(self):
        for col in self._cols:
            col.remove_selection()

class CalendarHeader(ttk.Frame):
    def __init__(self, master, draw_button, func_prev_month, func_next_month):
        ttk.Frame.__init__(self, master)
        if draw_button:
            lbtn = ttk.Button(self, style='L.TButton', command=func_prev_month)
            rbtn = ttk.Button(self, style='R.TButton', command=func_next_month)
        self._header = ttk.Label(self, width=15, anchor='center')
        self.pack(in_=master, side='top', pady=4, anchor='center')
        if draw_button:
            lbtn.grid(in_=self)
            self._header.grid(in_=self, column=1, row=0, padx=12)
            rbtn.grid(in_=self, column=2, row=0)
        else:
            self._header.grid(in_=self, column=1, row=0, padx=22)

    def build(self, text):
        self._header['text'] = text

class Calendar(ttk.Frame):
    datetime = calendar.datetime.datetime
    timedelta = calendar.datetime.timedelta

    def __init__(self, master, draw_button, func_prev_month, func_next_month):
        ttk.Frame.__init__(self, master)
        self._header = CalendarHeader(self, draw_button, func_prev_month, func_next_month)
        self._calendar = CalendarMonth(self)
        self._date = self.datetime(self.datetime.now().year, self.datetime.now().month, 1)

    def config(self, locale, font, config):
        if locale is None:
            self._cal = calendar.TextCalendar(config.firstweekday)
        else:
            self._cal = calendar.LocaleTextCalendar(config.firstweekday, locale)
        cols = self._cal.formatweekheader(3).split()
        self._calendar.config(cols, font, config)

    def build(self):
        year, month = self._date.year, self._date.month
        header = self._cal.formatmonthname(year, month, 0)
        self._header.build(header.title())
        weeks = self._cal.monthdayscalendar(year, month)
        self._calendar.build(weeks)

    def prev_month(self):
        self._calendar.remove_selection()
        self._date = self._date - self.timedelta(days=1)
        self._date = self.datetime(self._date.year, self._date.month, 1)
        self.build()

    def next_month(self):
        self._calendar.remove_selection()
        year, month = self._date.year, self._date.month
        self._date = self._date + self.timedelta(
            days=calendar.monthrange(year, month)[1] + 1)
        self._date = self.datetime(self._date.year, self._date.month, 1)
        self.build()

class OrgCaledar(ttk.Frame):
    def __init__(self, master=None, **kw):
        locale = kw.pop('locale', None)
        self._config = CalendarConfig()
        self._selection = None

        ttk.Frame.__init__(self, master, **kw)

        self.__setup_styles()
        self._calendars = []
        for it in range(3):
            draw_buttons = (it == 1)
            cal = Calendar(self, draw_buttons, self._prev_month, self._next_month)
            cal.grid(row=0, column=it)
            cal.config(locale, self._font, self._config)
            cal.build()
            self._calendars.append(cal)
        self._calendars[0].prev_month()
        self._calendars[2].next_month()

    def __setup_styles(self):
        self._font = tkFont.Font()
        style = ttk.Style(self.master)
        style.layout("Treeview", [('Treeview.treearea', {'sticky': 'nswe'})])
        arrow_layout = lambda dir: (
            [('Button.focus', {'children': [('Button.%sarrow' % dir, None)]})]
        )
        style.layout('L.TButton', arrow_layout('left'))
        style.layout('R.TButton', arrow_layout('right'))

    def _prev_month(self):
        [it.prev_month() for it in self._calendars]

    def _next_month(self):
        [it.next_month() for it in self._calendars]
