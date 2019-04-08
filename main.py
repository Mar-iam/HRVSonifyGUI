from tkinter import *
from hrv.classical import *
import time, math
import Pmw
import pygame.midi

domains = ['Time', 'Frequency', 'Nonlinear']
params = {'Time': ['SDNN', 'RMSSD', 'PNN50'],
          'Frequency': ['HF', 'LF', 'HF/LF'],
          'Nonlinear': ['SD1']}

# list retrieved from http://wiki.skoogmusic.com/manual/manual1.1/Skoog-Window/navigation/MIDI-Tab/index
instruments_lbl = ['Grand Piano', 'Xylophone', 'Accordion', 'Guitar', 'Violin', ]
instruments_values = [0, 13, 21, 28, 40]


class Window:
    def __init__(self, master, p):
        # initialise parameters
        self.filename = ''
        self.rr_filtered = []
        self.analysis_type = ''
        self.analysis_param = ''
        self.param_list = []
        self.ins_id = 0
        self.player = p
        self.file_info = 0

        self.displayVar = StringVar()
        self.displayVar.set('')

        # section 1: browse file
        self.f_label = Label(root, text="RR File", anchor='e').grid(row=1, column=1, sticky=W, padx=10)
        self.f_bar = Entry(master)
        self.f_bar.grid(row=1, column=2, columnspan=3, sticky=W+E)

        self.view_info = Label(root, textvariable=self.displayVar)
        self.view_info.grid(row=2, rowspan=2, column=5)

        self.browse_btn = Button(root, text="Browse", width=15, command=self.browse_file)
        self.browse_btn.grid(row=1, column=5, padx=10, pady=10)

        # section 2: HRV analysis parameters
        self.varDomain = StringVar()
        self.varParam = StringVar()

        self.varDomain.set('')
        self.varParam.set('')

        self.domain_menu = Pmw.OptionMenu(root,
                                          labelpos='w',
                                          label_text='Domain',
                                          items=domains,
                                          menubutton_textvariable=self.varDomain,
                                          menubutton_width=12,
                                          command=self.select_domain,
                                          )
        self.domain_menu.grid(row=2, column=1, columnspan=2, padx=10, pady=10)

        self.params_menu = Pmw.OptionMenu(root,
                                          labelpos='w',
                                          label_text='Parameter',
                                          items=params['Time'],
                                          menubutton_textvariable=self.varParam,
                                          menubutton_width=12,
                                          command=self.select_param,
                                          )
        self.params_menu.grid(row=2, column=3, columnspan=2, padx=10, pady=10)

        self.window_size_lbl = Label(root, text="Window Size").grid(row=3, column=1)
        self.window_size_scale = Scale(root,
                                       from_=5,
                                       to=10,
                                       orient= HORIZONTAL,
                                       command=self.get_window)

        self.window_size_scale.grid(row=3, column=2, padx=10)
        self.wnd_size = self.window_size_scale.get()

        self.varInc = StringVar()
        self.varInc.set('')

        inc_lbl = ["10 s", "30 s", "1 min", "2 min", "5 min"]
        inc_values = [0.2, 0.5, 1, 2, 5]
        self.inc_dict = dict(zip(inc_lbl, inc_values))
        # self.inc = 1

        self.inc_menu = Pmw.OptionMenu(root,
                                       labelpos='w',
                                       label_text='Increment',
                                       items=inc_lbl,
                                       menubutton_textvariable=self.varInc,
                                       menubutton_width=12,
                                       command=self.get_increment)
        self.inc_menu.grid(row=3, column=3, columnspan=2, padx=10, pady=10)

        self.process_btn = Button(root, text="Analyse RR", width=20, command=self.process_file)
        self.process_btn.grid(row=4, column=1, pady=10, columnspan=4)

        self.varIns = StringVar()
        self.varIns.set('')

        self.instr_dict = dict(zip(instruments_lbl, instruments_values))

        self.instr_menu = Pmw.OptionMenu(root,
                                         labelpos='w',
                                         label_text='Instrument',
                                         items=instruments_lbl,
                                         menubutton_textvariable=self.varIns,
                                         menubutton_width=10,
                                         command=self.get_instrument)

        self.instr_menu.grid(row=5, column=1, columnspan=2, pady=10)


        self.sonify_btn = Button(root, text="Sonify", width=15, command=self.sonify)
        self.sonify_btn.grid(
            row=5,
            column=3,
            columnspan=2,
            padx=10,
            pady=10)


    # Based on the selected domain, the displayed parameter list will be changed accordingly
    def select_domain(self, option):
        self.analysis_type = self.varDomain.get()
        param = params[self.varDomain.get()]
        self.params_menu.setitems(param)

        if not self.varParam.get() in param:
            self.varParam.set('')
            self.analysis_param = ''

    # Based on the selected parameter, the appropriate analysis will be conducted
    def select_param(self, option):
        self.analysis_param = self.varParam.get()

    def get_window(self, option):
        self.wnd_size = self.window_size_scale.get()

    def get_increment(self, option):
        self.inc = float(self.inc_dict[self.varInc.get()])
        print(self.inc)

    def get_instrument(self, option):
        self.ins_id = int(self.instr_dict[self.varIns.get()])

    def browse_file(self):
        import tkinter.filedialog as tkf
        from tkinter import messagebox

        self.filename = tkf.askopenfilename(filetypes= (("Text Files", "*.txt"), ("All files", "*.*") ))
        # self.filename = 'ironman/I2.txt'

        if not (self.filename).endswith(".txt"):
            messagebox.showerror("File Type Error", "Failed to read file " + self.filename +
                                 "\nFile type must be a '.txt'")
            return

        # TODO: check file content
        self.f_bar.delete(0, END)
        self.f_bar.insert(0, self.filename)
        self.rr_filtered = self.read_signal()

    def read_signal(self):
        if self.filename:
            with open(self.filename, 'r') as f:
                rr_list = f.read().splitlines()

                # Convert string to float
                rr_num = [float(rr) for rr in rr_list]

            rr_filtered = self.filter_signal(rr_num)

            trr = [(sum(rr_filtered[:i + 1]) / 1000) / 60 for i in range(len(rr_filtered))]
            self.displayVar.set('File information: \n' +
                                'Duration: ' +
                                str(round(trr[len(trr)-1],1)) +
                                ' minutes')  # minutes

        return rr_filtered

    @staticmethod
    def filter_signal(signal):
        ectopic = [i for i, j in enumerate(signal) if j >= 2000]

        for i in range(len(ectopic)):
            signal[ectopic[i]] = 0.5 * (signal[ectopic[i] - 1] + signal[ectopic[i] + 1])

        return signal

    @staticmethod
    def linear_mapping(value, smin, smax):
        vmin, vmax = min(value), max(value)
        mapped = [int(smin + ((v - vmin) / (vmax - vmin))*(smax - smin)) for v in value]

        return mapped

    @staticmethod
    def log_mapping(value, smin, smax):
        # This mapping has not been tested yet
        vmin, vmax = min(value), max(value)
        mapped = [int(smin + (math.log(v/vmin) / math.log(vmax/vmin)) * (smax - smin)) for v in value ]

        return mapped

    def analyse_signal(self, rr, anal_type):
        # TODO: multiple analysis types
        if anal_type == 'time':
            result = time_domain(rr)

        elif anal_type == 'frequency':
            result = frequency_domain(rr)

        elif anal_type == 'nonlinear':
            result = non_linear(rr)

        else:
            result = "Invalid Analysis Type"

        return result

    def move_window(self, ratio, signal, start_min, end_min):
        rr = signal[start_min * ratio:end_min * ratio]  # extract the required duration
        tw_min = self.wnd_size

        tw = tw_min * ratio  # number of samples in specified time window
        inc = int(self.inc * ratio)  # number of samples in each increment

        start = 0  # start index
        count = 0

        freq_analysis = []
        time_analysis = []
        nonlinear_analysis = []

        rr_avg = []

        for i in range(0, len(rr), inc):
            last = tw + start  # last index on each segment
            if last >= len(rr):
                break

            rr_analyse = rr[start:last]

            start += inc

            time_analysis.append(self.analyse_signal(rr_analyse, 'time'))
            freq_analysis.append(self.analyse_signal(rr_analyse, 'frequency'))
            nonlinear_analysis.append(self.analyse_signal(rr_analyse,'nonlinear'))

            rr_avg.append(np.mean(rr_analyse))

            # for debugging
            count += 1

        return time_analysis, freq_analysis, nonlinear_analysis

    def play_sound(self, mapped):
        self.player.set_instrument(self.ins_id)

        for i in range(len(mapped)):
            self.player.note_on(mapped[i], 127)
            time.sleep(0.5)
            self.player.note_off(mapped[i], 127)

    @staticmethod
    def get_lists(rr_dict, key):
        rr_list = [rr_dict[i][key] for i in range(len(rr_dict))]

        return rr_list

    def process_file(self):
        if self.filename and self.analysis_param:
            start_min = 10
            length = 20
            end_min = start_min + length
            # inc_min = 1

            trr = [(sum(self.rr_filtered[:i + 1]) / 1000) / 60 for i in range(len(self.rr_filtered))]  # minutes
            r = int(len(self.rr_filtered) / (trr[len(trr) - 1]))  # total number of samples in 1 minute

            time, freq, nonlinear = self.move_window(r, self.rr_filtered, start_min, end_min)

            print(self.analysis_type)
            if self.analysis_type == domains[0]:
                domain = time
            elif self.analysis_type == domains[1]:
                domain =freq
            else:
                domain = nonlinear

            self.param_list = self.get_lists(domain, self.analysis_param.lower())
            print('param_list: ', self.param_list)

    def sonify(self):
        if self.filename and len(self.param_list) != 0:
            smin, smax = 60, 100
            mapped = self.linear_mapping(self.param_list, smin, smax)
            print('mapped: ', mapped)

            self.play_sound(mapped)


def combine_funcs(*funcs):
    def combined_func(*args, **kwargs):
        for f in funcs:
            f(*args, **kwargs)

    return combined_func


if __name__ == '__main__':
    pygame.midi.init()
    player = pygame.midi.Output(0)

    root = Tk()
    Pmw.initialise(root)

    widget = Window(root, player)
    OK_btn = Button(root, text='Quit', width=20, command=root.destroy).grid(row=6, column=1, columnspan=4, pady=20)
    OK_btn = Button(root, text='Quit', width=20, command=root.destroy).grid(row=6, column=1, columnspan=4, pady=20)

    root.mainloop()
