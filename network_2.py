import queue
import threading
import json


## wrapper class for a queue of packets
class Interface:
    ## @param maxsize - the maximum size of the queue storing packets
    def __init__(self, maxsize=0):
        self.in_queue = queue.Queue(maxsize)
        self.out_queue = queue.Queue(maxsize)
    
    ##get packet from the queue interface
    # @param in_or_out - use 'in' or 'out' interface
    def get(self, in_or_out):
        try:
            if in_or_out == 'in':
                pkt_S = self.in_queue.get(False)
                # if pkt_S is not None:
                #     print('getting packet from the IN queue')
                return pkt_S
            else:
                pkt_S = self.out_queue.get(False)
                # if pkt_S is not None:
                #     print('getting packet from the OUT queue')
                return pkt_S
        except queue.Empty:
            return None
        
    ##put the packet into the interface queue
    # @param pkt - Packet to be inserted into the queue
    # @param in_or_out - use 'in' or 'out' interface
    # @param block - if True, block until room in queue, if False may throw queue.Full exception
    def put(self, pkt, in_or_out, block=False):
        if in_or_out == 'out':
            # print('putting packet in the OUT queue')
            self.out_queue.put(pkt, block)
        else:
            # print('putting packet in the IN queue')
            self.in_queue.put(pkt, block)
            
        
## Implements a network layer packet.
class NetworkPacket:
    ## packet encoding lengths 
    dst_S_length = 5
    prot_S_length = 1
    
    ##@param dst: address of the destination host
    # @param data_S: packet payload
    # @param prot_S: upper layer protocol for the packet (data, or control)
    def __init__(self, dst, prot_S, data_S):
        self.dst = dst
        self.data_S = data_S
        self.prot_S = prot_S
        
    ## called when printing the object
    def __str__(self):
        return self.to_byte_S()
        
    ## convert packet to a byte string for transmission over links
    def to_byte_S(self):
        byte_S = str(self.dst).zfill(self.dst_S_length)
        if self.prot_S == 'data':
            byte_S += '1'
        elif self.prot_S == 'control':
            byte_S += '2'
        else:
            raise('%s: unknown prot_S option: %s' %(self, self.prot_S))
        byte_S += self.data_S
        return byte_S
    
    ## extract a packet object from a byte string
    # @param byte_S: byte string representation of the packet
    @classmethod
    def from_byte_S(self, byte_S):
        dst = byte_S[0 : NetworkPacket.dst_S_length].strip('0')
        prot_S = byte_S[NetworkPacket.dst_S_length : NetworkPacket.dst_S_length + NetworkPacket.prot_S_length]
        if prot_S == '1':
            prot_S = 'data'
        elif prot_S == '2':
            prot_S = 'control'
        else:
            raise('%s: unknown prot_S field: %s' %(self, prot_S))
        data_S = byte_S[NetworkPacket.dst_S_length + NetworkPacket.prot_S_length : ]        
        return self(dst, prot_S, data_S)
    

    

## Implements a network host for receiving and transmitting data
class Host:
    
    ##@param addr: address of this node represented as an integer
    def __init__(self, addr):
        self.addr = addr
        self.intf_L = [Interface()]
        self.stop = False #for thread termination
    
    ## called when printing the object
    def __str__(self):
        return self.addr
       
    ## create a packet and enqueue for transmission
    # @param dst: destination address for the packet
    # @param data_S: data being transmitted to the network layer
    def udt_send(self, dst, data_S):
        p = NetworkPacket(dst, 'data', data_S)
        print('%s: sending packet "%s"' % (self, p))
        self.intf_L[0].put(p.to_byte_S(), 'out') #send packets always enqueued successfully
        
    ## receive packet from the network layer
    def udt_receive(self):
        pkt_S = self.intf_L[0].get('in')
        if pkt_S is not None:
            print('%s: received packet "%s"' % (self, pkt_S))
            if self.addr is 'H2':
                self.udt_send('H1', 'REPLY_FROM_H2')
       
    ## thread target for the host to keep receiving data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            #receive data arriving to the in interface
            self.udt_receive()
            #terminate
            if(self.stop):
                print (threading.currentThread().getName() + ': Ending')
                return
        


## Implements a multi-interface router
class Router:
    
    ##@param name: friendly router name for debugging
    # @param cost_D: cost table to neighbors {neighbor: {interface: cost}}
    # @param max_queue_size: max queue length (passed to Interface)
    def __init__(self, name, cost_D, max_queue_size):
        self.stop = False #for thread termination
        self.name = name
        #create a list of interfaces
        self.intf_L = [Interface(max_queue_size) for _ in range(len(cost_D))]
        #save neighbors and interfeces on which we connect to them
        self.cost_D = cost_D    # {neighbor: {interface: cost}}
        # Done: set up the routing table for connected hosts

        # initialize dictionary
        self.rt_tbl_D = {}

        # for each neighbor by connected interface
        for neighbor in cost_D.keys():
            # for each interface id
            for interface in cost_D[neighbor].keys():
                # update routing table to reflect cost to that neighbor from self
                self.rt_tbl_D.update({neighbor: {self.name: cost_D[neighbor][interface]}})

        # add self to routing table at cost 0 for completeness/updating
        self.rt_tbl_D.update({str(self): {str(self): 0}})    # {destination: {router: cost}}
        print('%s: Initialized routing table' % self)
        self.print_routes()


    ## called when printing the object
    def __str__(self):
        return self.name


    ## look through the content of incoming interfaces and 
    # process data and control packets
    def process_queues(self):
        for i in range(len(self.intf_L)):
            pkt_S = None
            #get packet from interface i
            pkt_S = self.intf_L[i].get('in')
            #if packet exists make a forwarding decision
            if pkt_S is not None:
                p = NetworkPacket.from_byte_S(pkt_S) #parse a packet out
                if p.prot_S == 'data':
                    self.forward_packet(p,i)
                elif p.prot_S == 'control':
                    self.update_routes(p, i)
                else:
                    raise Exception('%s: Unknown packet type in packet %s' % (self, p))
            

    ## forward the packet according to the routing table
    #  @param p Packet to forward
    #  @param i Incoming interface number for packet p
    def forward_packet(self, p, i):
        try:
            # Done: Here you will need to implement a lookup into the
            # forwarding table to find the appropriate outgoing interface
            # for now we assume the outgoing interface is 1

            # set shortest to largest value and path to meaningless value
            shortest = 9
            path = 9

            # for each router capable of getting to the destination
            for router in self.rt_tbl_D[p.dst]:
                # skipping this router since we cannot send packets to ourselves
                if router == self.name:
                    continue

                # get the cost of the route
                test_cost = self.rt_tbl_D[p.dst][router]

                # if it is less than the current shortest update
                if shortest > test_cost:
                    shortest = test_cost
                    for interface in self.cost_D[router]:
                        path = interface

            # for each neighbor
            for neighbor in self.cost_D:
                # check if the neighbor is the destination
                if p.dst == neighbor:
                    # get the interface
                    for interface in self.cost_D[neighbor]:
                        path = interface

            # send the packet on the shortest interface
            self.intf_L[path].put(p.to_byte_S(), 'out', True)

            print('%s: forwarding packet "%s" from interface %d to %d' % \
                (self, p, i, path))
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass


    ## send out route update
    # @param i Interface number on which to send out a routing update
    def send_routes(self, i):
        # Done: Send out a routing table update
        # create a routing table update packet

        # create an empty dictionary
        dist = {}
        # for each destination
        for destination in self.rt_tbl_D:
            # initialize dictionary at destination
            dist[destination] = {}
            # add the cost to this destination as the cost to get there from this location
            dist[destination][self.name] = self.rt_tbl_D[destination][self.name]

        # json turns dictionaries into strings
        s = json.dumps(dist)

        # send the packet with the table info in DV form
        p = NetworkPacket(0, 'control', s)
        try:
            print('%s: sending routing update "%s" from interface %d' % (self, p, i))
            self.intf_L[i].put(p.to_byte_S(), 'out', True)
        except queue.Full:
            print('%s: packet "%s" lost on interface %d' % (self, p, i))
            pass


    ## forward the packet according to the routing table
    #  @param p Packet containing routing information
    def update_routes(self, p, i):
        #Done: add logic to update the routing tables and
        # possibly send out routing updates
        print('%s: Received routing update %s from interface %d' % (self, p, i))

        # get distance table as a dictionary by json loads
        dist = json.loads(p.data_S)

        need_to_update = False

        # for each destination in Distance vector (other routers destination list)
        for destination in dist.keys():
            # for the sending router named route (single router sending updates)
            for route in dist[destination]:
                # if self does not contain this destination, add it
                if destination not in self.rt_tbl_D:
                    # at DV cost
                    self.rt_tbl_D[destination] = {}

                # and set how each router can reach new node
                self.rt_tbl_D[destination][route] = dist[destination][route]

        # for each destination in current routing table
        for destination in self.rt_tbl_D:
            # if we are destination -> skip
            if destination == self.name:
                continue

            min = 100
            # if current router has link to host it has the shortest path
            if self.name in self.rt_tbl_D[destination]:
                min = self.rt_tbl_D[destination][self.name]

            for route in self.rt_tbl_D[destination]:
                # if we are the route cost is cost by us
                if route == self.name:
                    cost = self.rt_tbl_D[destination][route]
                # otherwise its our cost plus the distance vector
                else:
                    cost = self.rt_tbl_D[destination][route] + self.rt_tbl_D[route][self.name]

                # if the minimum changed update the minimum
                if cost < min:
                    need_to_update = True
                    # update current cost
                    min = cost
            # update routing table (possibly back to old numbers)
            self.rt_tbl_D[destination][self.name] = min

        if need_to_update:
            # update neighbors
            for dest in self.cost_D.keys():
                for interface in self.cost_D[dest]:
                    self.send_routes(interface)
        
    ## Print routing table
    def print_routes(self):
        # Done: print the routes as a two dimensional table

        header = "  " + str(self) + " | "
        route = []
        # gets the full header and sets the first destination to get router list
        for destination in self.rt_tbl_D.keys():
            header = header + destination + " | "
            # gets each router
            for router in self.rt_tbl_D[destination].keys():
                if router not in route:
                    route.append(router)
        print(header)

        # print each row
        for router in route:
            row = "| " + router + " |  "
            for dest in self.rt_tbl_D.keys():
                row = row + str(self.rt_tbl_D[dest][router]) + " |  "
            print(row)

        print("")
                
    ## thread target for the host to keep forwarding data
    def run(self):
        print (threading.currentThread().getName() + ': Starting')
        while True:
            self.process_queues()
            if self.stop:
                print (threading.currentThread().getName() + ': Ending')
                return 
