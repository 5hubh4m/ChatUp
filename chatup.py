#!/usr/bin/env python2.7

import Tkinter                      #Tkinter GUI module
import ttk                          #themed tkinter module

import socket                       #Socket module

import select                       #Efficient I/O

import threading                    #Concurrency

import platform                     #For platform.platform()
import os                           #For os.system()

import ast                          #For ast.literal_eval()

#Message format: %@%dest_nick_name%@%message%&%sender_nick_name%&%

def get_nick(msg):
    msg = msg[: -3]
    return msg[msg.rfind('%&%') + 3 :]

def get_dest(msg):
    msg = msg[3 :]
    return msg[: msg.find('%@%')]

def get_message(msg):
    msg = msg[3 : -3]
    return msg[msg.find('%@%') + 3 : msg.rfind('%&%')]

color = ['red', 'blue', 'green', 'pink', 'yellow', 'grey', 'magenta', 'orange', 'purple', 'violet', 'indigo']

def color_hash(str):
    result = 0
    a = ord(str[0])
    for c in str[1:]:
        b = ord(c)
        result = result + a * b
        a = b

    return result % 10

class Application(Tkinter.Tk):
    def launch_app(self):
        self.title('ChatUp')

        self.frame = ttk.Frame(self)

        self.frame.style = ttk.Style()

        self.server_button = ttk.Button(self.frame, text = 'Launch Server', command = self.launch_server)
        self.client_button = ttk.Button(self.frame, text = 'Launch Client', command = self.client_menu)

        self.server_button.grid(row = 0, column = 0, columnspan = 2, rowspan = 2, padx = 40, pady = 30)
        self.client_button.grid(row = 2, column = 0, columnspan = 2, rowspan = 2, padx = 40, pady = 30)

        self.frame.pack(fill = Tkinter.BOTH, expand = True)

        if platform.platform()[:6] == 'Darwin':
            self.theme_use = 'aqua'

            os.system("""/usr/bin/osascript -e 'tell app "Finder" to set frontmost of process "Python" to true'""")

        else:
            self.theme_use = 'default'

            self.lift()

        self.frame.style.theme_use(self.theme_use)

        self.mainloop()

    def client_menu(self):
        self.client_button.destroy()
        self.server_button.destroy()

        self.host_entry_label = ttk.Label(self.frame, text = 'Server Host Name/IP Address', anchor = Tkinter.W, justify = Tkinter.LEFT)
        self.host_entry = ttk.Entry(self.frame)

        self.nick_entry_label = ttk.Label(self.frame, text = 'Nick Name', anchor = Tkinter.W, justify = Tkinter.LEFT)
        self.nick_entry = ttk.Entry(self.frame)

        self.launch_button = ttk.Button(self.frame, text = 'Launch as Client!', command = self.launch_client)

        self.host_entry_label.grid(row = 0, column = 0, pady = 10, padx = 5)
        self.host_entry.grid(row = 0, column = 1, pady = 10, padx = 5)
        self.nick_entry_label.grid(row = 1, column = 0, pady = 10, padx = 5)
        self.nick_entry.grid(row = 1, column = 1, pady = 10, padx = 5)
        self.launch_button.grid(row = 2, column = 0, columnspan = 2, pady = 10, padx = 5)

        self.host_entry.focus_set()

    def launch_client(self):
        self.host = self.host_entry.get()
        self.port = 15000
        self.nick = self.nick_entry.get()

        self.host_entry_label.destroy()
        self.host_entry.destroy()
        self.nick_entry_label.destroy()
        self.nick_entry.destroy()
        self.launch_button.destroy()
        self.frame.pack_forget()

        self.title('ChatUp Client: {0}'.format(self.nick))

        self.should_quit = False

        self.protocol('WM_DELETE_WINDOW', self.client_quit)

        self.chat_frame = ttk.Frame(self.frame, borderwidth = 5)
        self.clients_frame = ttk.Frame(self.frame)
        self.entry_frame = ttk.Frame(self)

        self.chat_frame.style = ttk.Style()
        self.chat_frame.style.theme_use(self.theme_use)
        self.clients_frame.style = ttk.Style()
        self.clients_frame.style.theme_use(self.theme_use)
        self.entry_frame.style = ttk.Style()
        self.entry_frame.style.theme_use(self.theme_use)

        self.chat_text = Tkinter.Text(self.chat_frame, state = Tkinter.DISABLED)

        self.chat_entry = ttk.Entry(self.entry_frame)
        self.send_button = ttk.Button(self.entry_frame, text = 'Send')

        self.send_button.bind('<Button-1>', self.send)
        self.chat_entry.bind('<Return>', self.send)

        self.entry_frame.pack(side = Tkinter.BOTTOM, fill = Tkinter.X)
        self.frame.pack(side = Tkinter.TOP, fill = Tkinter.BOTH, expand = True)
        self.clients_frame.pack(side = Tkinter.LEFT, fill = Tkinter.BOTH, expand = True)
        self.chat_frame.pack(side = Tkinter.RIGHT, fill = Tkinter.BOTH, expand = True)

        self.chat_entry.pack(side = Tkinter.LEFT, fill = Tkinter.X, expand = True)
        self.send_button.pack(side = Tkinter.RIGHT)

        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.client_socket.connect((self.host, self.port))
        self.client_socket.send('Please allow connection!%&%{0}%&%'.format(self.nick))
        self.clients = ast.literal_eval(self.client_socket.recv(1024)[11 : ])

        self.dest = Tkinter.StringVar()
        self.radios = []

        self.radio_label = ttk.Label(self.clients_frame,
                    width = 15,
                    wraplength = 125,
                    anchor = Tkinter.W,
                    justify = Tkinter.LEFT,
                    text = 'Choose reciever from the following connected clients:')

        self.radio_label.pack()
        self.chat_text.pack(fill = Tkinter.BOTH, expand = True)

        self.__i = 0
        self.__j = 1

        for client in self.clients:
            r = ttk.Radiobutton(self.clients_frame, text = client, variable = self.dest, value = client)
            r.pack(anchor = Tkinter.W)

            self.radios.append(r)

        self.dest.set(self.clients[0])

        self.chat_entry.focus_set()

        self.clientd_thread = threading.Thread(name = 'clientd', target = self.clientd)

        self.clientd_thread.start()

    def send(self, event):
        message = self.chat_entry.get()
        dest = self.dest.get()
        data = '%@%{0}%@%{1}%&%{2}%&%'.format(dest, message, self.nick)

        self.chat_entry.delete(0, Tkinter.END)

        self.client_socket.send(data)

        self.chat_text.config(state = Tkinter.NORMAL)
        self.chat_text.insert(Tkinter.END, 'To {0}'.format(dest, message), ('tag{0}'.format(self.__i)))
        self.chat_text.insert(Tkinter.END, ': {0}\n'.format(message), ('tag{0}'.format(self.__j)))
        self.chat_text.tag_config('tag{0}'.format(self.__i), justify = Tkinter.RIGHT, foreground = color[color_hash(dest)], font = 'Times 14 bold', underline = True)
        self.chat_text.tag_config('tag{0}'.format(self.__j), justify = Tkinter.RIGHT, foreground = 'black')
        self.chat_text.config(state = Tkinter.DISABLED)

        self.__i = self.__i + 2
        self.__j = self.__j + 2

        self.chat_text.see(Tkinter.END)

    def clientd(self):
        while not self.should_quit:
            try:
                data = self.client_socket.recv(1024)

                if len(data):
                    if data[ : 11] == 'clientlist:':
                        self.clients = ast.literal_eval(data[11 : ])

                        for r in self.radios:
                            r.destroy()

                        for client in self.clients:
                            r = ttk.Radiobutton(self.clients_frame, text = client, variable = self.dest, value = client)
                            r.pack(anchor = Tkinter.W)

                            self.radios.append(r)

                    else:
                        sender = get_nick(data)
                        message = get_message(data)

                        self.chat_text.config(state = Tkinter.NORMAL)
                        self.chat_text.insert(Tkinter.END, 'From {0}'.format(sender), ('tag{0}'.format(self.__i)))
                        self.chat_text.insert(Tkinter.END, ': {0}\n'.format(message), ('tag{0}'.format(self.__j)))
                        self.chat_text.tag_config('tag{0}'.format(self.__i), justify = Tkinter.LEFT, foreground = color[color_hash(sender)], font = 'Times 14 bold', underline = True)
                        self.chat_text.tag_config('tag{0}'.format(self.__j), justify = Tkinter.LEFT, foreground = 'black')
                        self.chat_text.config(state = Tkinter.DISABLED)

                        self.__i = self.__i + 2
                        self.__j = self.__j + 2

                        self.chat_text.see(Tkinter.END)

                else:
                    break

            except:
                continue

    def launch_server(self):
        self.client_button.destroy()
        self.server_button.destroy()

        self.host = '0.0.0.0'
        self.port = 15000

        self.title('ChatUp Server Log')

        self.log_frame = ttk.Frame(self)

        self.log_frame.style = ttk.Style()
        self.log_frame.style.theme_use(self.theme_use)

        msg = 'Server running at {0}:{1}.'.format(self.host, self.port)

        self.server_message = ttk.Label(self.frame, text = msg)
        self.server_log = Tkinter.Text(self.log_frame, state = Tkinter.DISABLED)

        self.server_log.pack(expand = True, fill = Tkinter.BOTH)

        self.server_message.pack()
        self.log_frame.pack(expand = True, fill = Tkinter.BOTH)

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.settimeout(0.2)
        self.server_socket.bind((self.host, self.port))

        self.client_sockets = {}    #Dictionary -> nick:socket
        self.clients = {}           #Dictionary -> address:nick_name

        self.serverd_thread = threading.Thread(name = 'serverd', target = self.serverd)
        self.client_comm_threads = []

        self.serverd_thread.start()

    def serverd(self):
        self.server_socket.listen(5)

        self.should_quit = False

        self.protocol('WM_DELETE_WINDOW', self.server_quit)

        while not self.should_quit:
            try:
                client, addr = self.server_socket.accept()

                client.settimeout(1.0)

                first_data = client.recv(1024)
                nick = get_nick(first_data)

                self.server_log.config(state = Tkinter.NORMAL)
                self.server_log.insert(Tkinter.INSERT, 'Nick {0} connected from {1}\n'.format(nick, addr))
                self.server_log.config(state = Tkinter.DISABLED)

                self.clients[addr] = nick
                self.client_sockets[nick] = client

                for name in self.client_sockets:
                    self.client_sockets[name].send('clientlist:' + str(self.client_sockets.keys()))

                t = threading.Thread(name = 'client {0}'.format(nick), target = self.socket_comm, args = (addr, ))

                t.start()

            except socket.timeout:
                continue

    def socket_comm(self, addr):
        nick = self.clients[addr]

        csocket = self.client_sockets[nick]

        while not self.should_quit:
            r, _, _ = select.select([csocket], [], [])
            if r:
                data = csocket.recv(1024)

                if len(data):
                    dest = get_dest(data)

                    if self.client_sockets.has_key(dest):
                        self.server_log.config(state = Tkinter.NORMAL)
                        self.server_log.insert(Tkinter.END, 'Sending msg from {0} to {1}\n'.format(nick, dest))
                        self.server_log.config(state = Tkinter.DISABLED)

                        self.client_sockets[dest].send(data)

                    else:
                        self.server_log.config(state = Tkinter.NORMAL)
                        self.server_log.insert(Tkinter.END, 'Invalid destination nick {0}\n'.format(dest))
                        self.server_log.config(state = Tkinter.DISABLED)

                else:
                    break
            else:
                continue

        self.server_log.config(state = Tkinter.NORMAL)
        self.server_log.insert(Tkinter.END, 'Connection from {0} at {1} dropped.\n'.format(nick, addr))
        self.server_log.config(state = Tkinter.DISABLED)

        csocket.close()

        self.client_sockets.pop(nick)
        self.clients.pop(addr)

        for name in self.client_sockets:
            self.client_sockets[name].send('clientlist:' + str(self.client_sockets.keys()))

    def server_quit(self):
        self.should_quit = True

        for t in self.client_comm_threads:
            t.join()

        self.serverd_thread.join()

        for nick in self.client_sockets:
            self.client_sockets[nick].close()

        self.server_socket.close()

        self.destroy()

    def client_quit(self):
        self.should_quit = True

        self.client_socket.shutdown(socket.SHUT_WR)

        self.clientd_thread.join()

        self.client_socket.close()

        self.destroy()

if __name__ == '__main__':
    app = Application()

    app.launch_app()
