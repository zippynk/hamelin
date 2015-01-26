from . import hamelin
import time
import threading
import socket
import select
import errno

import sys

class netdaemon(hamelin.daemon):
    def run(self, host='', port=8080):
        print("Running at host %s on port %d"%(host, port))
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((host, port))
        s.listen(5)
        while True:
            time.sleep(0)
            accepted = s.accept()
            t = threading.Thread(
                target = self.server_loop,
                args   = accepted,
                name   = "net-server-%s:%d"%accepted[1])
            t.start()

    def server_loop(self, conn, add):
        serv = self.create_server({
            'H-VERSION': 'HAMELIN.PY-NET-0.1',
            'H-CLIENT': add[0]+":"+str(add[1])
        })
         
        conn.setblocking(0)
        def recv(text):
            r, w, e = select.select([conn], [conn], [conn])
            if len(w) == 1:
                current = text
                while len(current) > 0:
                    try:
                        size = conn.send(current)
                        current = current[size:]
                        if size == 0:
                            print("Sent nothing. Killing server.")
                            serv.kill()
                            break
                    except socket.error:
                        print("Write failed with error. Killing server.")
                        serv.kill()
                        break
            else:
                print("Yikes can't write.")

        def quit(code):
            conn.close()

        serv.handle_data = recv
        serv.handle_quit = quit
        serv.startup()
        totalgot = 0
        while serv.alive:
            time.sleep(0)
            r, w, e = select.select([conn], [conn], [conn], 1)
            if len(e) > 0:
                print("Something is on fire.")
            if len(w) == 0:
                print("Dead?")
            if len(r) > 0:
                try:
                    d = conn.recv(4096)
                    totalgot += len(d)
                    if len(d) == 0:
                        serv.eof()
                    else:
                        serv.send(d)
                except socket.error as err:
                    if err.errno == errno.ECONNRESET:
                        print("Connection reset.")
                    print("Oh no, the socket died and threw an error.")
                    serv.kill()
                    break
                except KeyboardInterrupt:
                    print("Yikes.")
                    serv.kill()
                    break

def main():
    if len(sys.argv) < 4:
        print("Usage: hamelin-net [host] [port] [args...]")
        exit(1)
    
    host = sys.argv[1]
    port = int(sys.argv[2])
    args = sys.argv[3:]
    netdaemon(args).run(host=host, port=port)

if __name__ == '__main__':
    d = netdaemon(['/usr/bin/grep', '--line-buffered', 'cow'])
    d.run(port=8080)
