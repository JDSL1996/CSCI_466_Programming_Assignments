<<<<<<< HEAD
import Network_3_0
=======
import Network
>>>>>>> 9208c7cf517c03c8f430b3d3890b9541e9d8f5fb
import argparse
from time import sleep
import hashlib
import time

<<<<<<< HEAD
=======

>>>>>>> 9208c7cf517c03c8f430b3d3890b9541e9d8f5fb
class Packet:
    ## the number of bytes used to store packet length
    seq_num_S_length = 10
    length_S_length = 10
    ## length of md5 checksum in hex
<<<<<<< HEAD
    checksum_length = 32 
=======
    checksum_length = 32
>>>>>>> 9208c7cf517c03c8f430b3d3890b9541e9d8f5fb
        
    def __init__(self, seq_num, msg_S):
        self.seq_num = seq_num
        self.msg_S = msg_S
        
    @classmethod
    def from_byte_S(self, byte_S):
        if Packet.corrupt(byte_S):
            raise RuntimeError('Cannot initialize Packet: byte_S is corrupt')
        #extract the fields
        seq_num = int(byte_S[Packet.length_S_length : Packet.length_S_length+Packet.seq_num_S_length])
        msg_S = byte_S[Packet.length_S_length+Packet.seq_num_S_length+Packet.checksum_length :]
        return self(seq_num, msg_S)
        
        
    def get_byte_S(self):
        #convert sequence number of a byte field of seq_num_S_length bytes
        seq_num_S = str(self.seq_num).zfill(self.seq_num_S_length)
        #convert length to a byte field of length_S_length bytes
        length_S = str(self.length_S_length + len(seq_num_S) + self.checksum_length + len(self.msg_S)).zfill(self.length_S_length)
        #compute the checksum
        checksum = hashlib.md5((length_S+seq_num_S+self.msg_S).encode('utf-8'))
        checksum_S = checksum.hexdigest()
        #compile into a string
        return length_S + seq_num_S + checksum_S + self.msg_S
<<<<<<< HEAD
   
=======

>>>>>>> 9208c7cf517c03c8f430b3d3890b9541e9d8f5fb
    
    @staticmethod
    def corrupt(byte_S):
        #extract the fields
        length_S = byte_S[0:Packet.length_S_length]
        seq_num_S = byte_S[Packet.length_S_length : Packet.seq_num_S_length+Packet.seq_num_S_length]
        checksum_S = byte_S[Packet.seq_num_S_length+Packet.seq_num_S_length : Packet.seq_num_S_length+Packet.length_S_length+Packet.checksum_length]
        msg_S = byte_S[Packet.seq_num_S_length+Packet.seq_num_S_length+Packet.checksum_length :]
        
        #compute the checksum locally
        checksum = hashlib.md5(str(length_S+seq_num_S+msg_S).encode('utf-8'))
        computed_checksum_S = checksum.hexdigest()
        #and check if the same
        return checksum_S != computed_checksum_S
        

class RDT:
    ## latest sequence number used in a packet
    seq_num = 1
    ## buffer of bytes read from network
    byte_buffer = '' 

    def __init__(self, role_S, server_S, port):
<<<<<<< HEAD
        self.network = Network_3_0.NetworkLayer(role_S, server_S, port)
=======
        self.network = Network.NetworkLayer(role_S, server_S, port)
>>>>>>> 9208c7cf517c03c8f430b3d3890b9541e9d8f5fb
    
    def disconnect(self):
        self.network.disconnect()
        
    def rdt_1_0_send(self, msg_S):
        p = Packet(self.seq_num, msg_S)
        self.seq_num += 1
        self.network.udt_send(p.get_byte_S())
        
    def rdt_1_0_receive(self):
        ret_S = None
        byte_S = self.network.udt_receive()
        self.byte_buffer += byte_S
        #keep extracting packets - if reordered, could get more than one
        while True:
            #check if we have received enough bytes
            if(len(self.byte_buffer) < Packet.length_S_length):
                return ret_S #not enough bytes to read packet length
            #extract length of packet
            length = int(self.byte_buffer[:Packet.length_S_length])
            if len(self.byte_buffer) < length:
                return ret_S #not enough bytes to read the whole packet
            #create packet from buffer content and add to return string
            p = Packet.from_byte_S(self.byte_buffer[0:length])
            ret_S = p.msg_S if (ret_S is None) else ret_S + p.msg_S
            #remove the packet bytes from the buffer
            self.byte_buffer = self.byte_buffer[length:]
            #if this was the last packet, will return on the next iteration
            
    
    def rdt_2_1_send(self, msg_S):
<<<<<<< HEAD
        p = Packet(self.seq_num, msg_S)
        self.network.udt_send(p.get_byte_S())

        # if sending ACK or NAK do not listen for ACK
        if msg_S != 'ACK' or msg_S != 'NAK':
            # listen for ACK

            # keep extracting packets - if reordered, could get more than one
            while True:
                # make a packet from the incoming data
                byte_S = self.network.udt_receive()
                self.byte_buffer += byte_S

                # check if we have received enough bytes
                if (len(self.byte_buffer) < Packet.length_S_length):
                    continue
                # extract length of packet
                length = int(self.byte_buffer[:Packet.length_S_length])
                if len(self.byte_buffer) < length:
                    continue

                # get info
                info = self.byte_buffer[0:length]

                # if the information is not corrupt
                if not Packet.corrupt(info):
                    # create packet from buffer content
                    ac = Packet.from_byte_S(info)

                    # if NAK resend message
                    if ac.msg_S == 'NAK':
                        # clear corrupt message
                        self.byte_buffer = self.byte_buffer[length:]
                        # resend data
                        self.network.udt_send(p.get_byte_S())
                        continue
                    # if ACK then move on
                    elif ac.msg_S == 'ACK':
                        # clear corrupt message
                        self.byte_buffer = self.byte_buffer[length:]
                        # update seq num
                        self.seq_num += 1
                        return None
                    else:
                        # clear message
                        self.byte_buffer = self.byte_buffer[length:]
                        return None

                # if corrupt
                else:
                    print 'Corruption Detected.'
                    # clear corrupt message
                    self.byte_buffer = self.byte_buffer[length:]
                    # resend data
                    self.network.udt_send(p.get_byte_S())
                    #continue


    def rdt_2_1_receive(self):
        ret_S = None
        # make a packet from the incoming data
        byte_S = self.network.udt_receive()
        self.byte_buffer += byte_S
        # keep extracting packets - if reordered, could get more than one
        while True:
            # check if we have received enough bytes
            if (len(self.byte_buffer) < Packet.length_S_length):
                return ret_S  # not enough bytes to read packet length
            # extract length of packet
            length = int(self.byte_buffer[:Packet.length_S_length])
            if len(self.byte_buffer) < length:
                return ret_S  # not enough bytes to read the whole packet
            # get all packet info
            info = self.byte_buffer[0:length]

            # remove the packet bytes from the buffer
            self.byte_buffer = self.byte_buffer[length:]

            # if the information is not corrupt
            if not Packet.corrupt(info):
                # create packet from buffer content
                p = Packet.from_byte_S(info)

                # if ACK of correct seq return to ignore
                if p.msg_S == 'ACK' or p.msg_S == 'NAK':
                    return None

                # if the sequence numbers match
                if p.seq_num == self.seq_num:

                    # create and send an ACK & increase seq num
                    ac = Packet(self.seq_num, 'ACK')

                    self.seq_num += 1

                    # actually send
                    self.network.udt_send(ac.get_byte_S())

                    # set the message to be returned
                    ret_S = p.msg_S
                    return ret_S  # return the message

                # if repeated data
                elif p.seq_num != self.seq_num:
                    # resend ACK
                    ac = Packet(p.seq_num, 'ACK')

                    self.network.udt_send(ac.get_byte_S())
                    return ret_S  # no usable data
            # if corrupt
            else:
               # send Nak
                print 'Corruption Detected.'
                nak = Packet(self.seq_num, 'NAK')
                self.network.udt_send(nak.get_byte_S())
                return None  # no usable data

=======
        pass

    def rdt_2_1_receive(self):
        pass
>>>>>>> 9208c7cf517c03c8f430b3d3890b9541e9d8f5fb
    
    def rdt_3_0_send(self, msg_S):
        timeout = 1  # send the next message if no response
        time_of_last_data = time.time()

        p = Packet(self.seq_num, msg_S)
        self.network.udt_send(p.get_byte_S())

        # if sending ACK or NAK do not listen for ACK
        if msg_S != 'ACK' or msg_S != 'NAK':
            # listen for ACK

            # keep extracting packets - if reordered, could get more than one
            while True:
                if time_of_last_data + timeout < time.time():
                    time_of_last_data = time.time()

                    # clear buffer
                    self.byte_buffer = ''

                    # resend data
                    self.network.udt_send(p.get_byte_S())
                    continue

                # make a packet from the incoming data
                byte_S = self.network.udt_receive()
                self.byte_buffer += byte_S

                # check if we have received enough bytes
                if (len(self.byte_buffer) < Packet.length_S_length):
                    continue

                # extract length of packet
                length = int(self.byte_buffer[:Packet.length_S_length])

                if len(self.byte_buffer) < length:
                    continue

                # get info
                info = self.byte_buffer[0:length]

                # if the information is not corrupt
                if not Packet.corrupt(info):
                    # create packet from buffer content
                    ac = Packet.from_byte_S(info)

                    # if NAK resend message
                    if ac.msg_S == 'NAK':
                        # clear message
                        self.byte_buffer = self.byte_buffer[length:]
                        # ignore repeat packets were not looking at
                        if ac.seq_num != self.seq_num:
                            continue
                        # resend data
                        self.network.udt_send(p.get_byte_S())
                        continue
                    # if ACK then move on
                    elif ac.msg_S == 'ACK':
                        # clear message
                        self.byte_buffer = self.byte_buffer[length:]
                        # ignore repeat packets were not looking at
                        if ac.seq_num != self.seq_num:
                            continue
                        # update seq num
                        self.seq_num += 1
                        return None
                    else:
                        # clear message
                        self.byte_buffer = self.byte_buffer[length:]
                        return

                # if corrupt
                else:
                    # clear corrupt message
                    self.byte_buffer = self.byte_buffer[length:]
                    # resend data
                    self.network.udt_send(p.get_byte_S())
<<<<<<< HEAD
=======

>>>>>>> 9208c7cf517c03c8f430b3d3890b9541e9d8f5fb
        
    def rdt_3_0_receive(self):
        ret_S = None
        # make a packet from the incoming data
        byte_S = self.network.udt_receive()
        self.byte_buffer += byte_S
        # keep extracting packets - if reordered, could get more than one
        while True:
            # check if we have received enough bytes
            if (len(self.byte_buffer) < Packet.length_S_length):
                return ret_S  # not enough bytes to read packet length
            # extract length of packet
            length = int(self.byte_buffer[:Packet.length_S_length])
            if len(self.byte_buffer) < length:
                return ret_S  # not enough bytes to read the whole packet
            # get all packet info
            info = self.byte_buffer[0:length]

            # remove the packet bytes from the buffer
            self.byte_buffer = self.byte_buffer[length:]

            # if the information is not corrupt
            if not Packet.corrupt(info):
                # create packet from buffer content
                p = Packet.from_byte_S(info)

                # if ACK return to ignore
                if p.msg_S == 'ACK' or p.msg_S == 'NAK':
                    return None

                # if the sequence numbers match
                if p.seq_num == self.seq_num:

                    # create and send an ACK & increase seq num
                    ac = Packet(self.seq_num, 'ACK')

                    self.seq_num += 1

                    # actually send
                    self.network.udt_send(ac.get_byte_S())

                    # set the message to be returned
                    ret_S = p.msg_S
                    return ret_S  # return the message

                # if repeated data
                elif p.seq_num != self.seq_num:
                    # resend ACK
                    ac = Packet(p.seq_num, 'ACK')

                    self.network.udt_send(ac.get_byte_S())
                    return ret_S  # no usable data
            # if corrupt
            else:
                # send Nak
                nak = Packet(self.seq_num, 'NAK')
                self.network.udt_send(nak.get_byte_S())
                return None  # no usable data
<<<<<<< HEAD
        
=======
>>>>>>> 9208c7cf517c03c8f430b3d3890b9541e9d8f5fb

if __name__ == '__main__':
    parser =  argparse.ArgumentParser(description='RDT implementation.')
    parser.add_argument('role', help='Role is either client or server.', choices=['client', 'server'])
    parser.add_argument('server', help='Server.')
    parser.add_argument('port', help='Port.', type=int)
    args = parser.parse_args()
    
    rdt = RDT(args.role, args.server, args.port)
    if args.role == 'client':
        rdt.rdt_1_0_send('MSG_FROM_CLIENT')
        sleep(2)
        print(rdt.rdt_1_0_receive())
        rdt.disconnect()
        
        
    else:
        sleep(1)
        print(rdt.rdt_1_0_receive())
        rdt.rdt_1_0_send('MSG_FROM_SERVER')
        rdt.disconnect()
        


        
        