##
# CSC 216 (Spring 2018)
# Reliable Transport Protocols (Homework 3)
#
# Sender-receiver code for the RDP simulation program.  You should provide
# your implementation for the homework in this file.
#
# Your various Sender implementations should inherit from the BaseSender
# class which exposes the following important methods you should use in your
# implementations:
#
# - sender.send_to_network(seg): sends the given segment to network to be
#   delivered to the appropriate recipient.
# - sender.start_timer(interval): starts a timer that will fire once interval
#   steps have passed in the simulation.  When the timer expires, the sender's
#   on_interrupt() method is called (which should be overridden in subclasses
#   if timer functionality is desired)
#
# Your various Receiver implementations should also inherit from the
# BaseReceiver class which exposes thef ollowing important methouds you should
# use in your implementations:
#
# - sender.send_to_network(seg): sends the given segment to network to be
#   delivered to the appropriate recipient.
# - sender.send_to_app(msg): sends the given message to receiver's application
#   layer (such a message has successfully traveled from sender to receiver)
#
# Subclasses of both BaseSender and BaseReceiver must implement various methods.
# See the NaiveSender and NaiveReceiver implementations below for more details.
##

from sendrecvbase import BaseSender, BaseReceiver

import Queue

WINDOW_SIZE = 3


class Segment:
    def __init__(self, msg, dst, alt_bit=None, sequence_num=0):
        self.msg = msg
        self.dst = dst
        self.alt_bit = alt_bit
        self.sequence_num = sequence_num


class NaiveSender(BaseSender):
    def __init__(self, app_interval):
        super(NaiveSender, self).__init__(app_interval)

    def receive_from_app(self, msg):
        seg = Segment(msg, 'receiver', False)
        self.send_to_network(seg)

    def receive_from_network(self, seg):
        pass    # Nothing to do!

    def on_interrupt(self):
        pass    # Nothing to do!


class NaiveReceiver(BaseReceiver):
    def __init__(self):
        super(NaiveReceiver, self).__init__()

    def receive_from_client(self, seg):
        self.send_to_app(seg.msg)


class AltSender(BaseSender):
    def __init__(self, app_interval):
        super(AltSender, self).__init__(app_interval)
        self.alt_bit = True
        self.cur_seg = Segment('', '', True)

    def receive_from_app(self, msg):
        #print(self.alt_bit)
        seg = Segment(msg, 'receiver', self.alt_bit)
        self.disallow_app_msgs()
        self.send_to_network(seg)
        self.start_timer(self.app_interval)
        self.cur_seg = seg

    def receive_from_network(self, seg):
        if seg.msg == 'ACK' and self.alt_bit == seg.alt_bit:
            #print('1')
            self.end_timer()
            self.alt_bit = not self.alt_bit
            self.allow_app_msgs()

        elif seg.msg == 'ACK' and self.alt_bit != seg.alt_bit:
            #print('2')
            #self.send_to_network(self.cur_seg)
            #self.start_timer(self.app_interval)
            self.on_interrupt()

        elif seg.msg == '<CORRUPTED>':
            #print("Can't happen...")
            #self.send_to_network(self.cur_seg)
            #self.start_timer(self.app_interval)
            self.on_interrupt()

    def on_interrupt(self):
        self.send_to_network(self.cur_seg)
        self.start_timer(self.app_interval)


class AltReceiver(BaseReceiver):
    def __init__(self):
        super(AltReceiver, self).__init__()
        self.alt_bit = True

    def receive_from_client(self, seg):
        if seg.msg == '<CORRUPTED>':
            self.send_to_network(Segment('ACK', 'sender', not self.alt_bit))

        elif self.alt_bit != seg.alt_bit:
            self.send_to_network(Segment('ACK', 'sender', not self.alt_bit))

        else:
            self.send_to_app(seg.msg)
            self.send_to_network(Segment('ACK', 'sender', self.alt_bit))
            self.alt_bit = not self.alt_bit


class GBNSender(BaseSender):
    def __init__(self, app_interval):
        super(GBNSender, self).__init__(app_interval)
        self.sequence_base = 0
        self.next_sequence = 0
        # Store the packets within the same sequence
        self.segments = [Segment('', 'receiver', True, 0)] * WINDOW_SIZE

    def receive_from_app(self, msg):
        #print(self.segments)
        # Next sequence is within length of whole cycle
        if self.next_sequence < self.sequence_base + WINDOW_SIZE:
            seg = Segment(msg, 'receiver', True, self.next_sequence)
            self.segments[self.next_sequence % WINDOW_SIZE] = seg
            print('sent')
            self.send_to_network(seg)
            if self.sequence_base == self.next_sequence:
                self.start_timer(self.app_interval)
            self.next_sequence += 1
            print('{} {}'.format(self.sequence_base, self.next_sequence))

        # Start the timer when the first packet of the sequence is sent

        # End of cycle
        else:
            self.disallow_app_msgs()

    def receive_from_network(self, seg):
        if seg.msg == 'ACK' and self.sequence_base == seg.sequence_num:
            #self.allow_app_msgs()
            print('Increment base. Base: {}, seg {}'.format(self.sequence_base, seg.sequence_num))
            self.sequence_base += 1
            # seg.sequence_num = self.next_sequence + 1
            if self.sequence_base == self.next_sequence:
                self.end_timer()
            else:
                self.start_timer(self.app_interval)
        elif seg.msg == 'ACK' and self.sequence_base == seg.sequence_num + 1:
            print('Base {}, seg {}'.format(self.sequence_base, seg.sequence_num))
            self.on_interrupt()

        #if seg.msg == 'ACK' and self.sequence_base != seg.sequence_num:
        ##    self.sequence_base = seg.sequence_num
        #    self.on_interrupt()

        # Next sequence is within the cycle
        #elif self.next_sequence - self.sequence_base <= WINDOW_SIZE:
        #    self.allow_app_msgs()

        # End of cycle
        #elif self.sequence_base == self.next_sequence:
        #   self.end_timer()

        # Start the time for every packet sent in the sequence
        #else:
        #    self.start_timer(self.app_interval)

    def on_interrupt(self):
        # Go back and retransmit the lost frame and subsequent frames within a cycle
        print ('interrupt')
        for i in range(self.sequence_base, self.next_sequence):
            self.send_to_network(self.segments[i % WINDOW_SIZE])
        self.start_timer(self.app_interval)


class GBNReceiver(BaseReceiver):
    def __init__(self):
        super(GBNReceiver, self).__init__()
        self.request_num = 0

    def receive_from_client(self, seg):
        if seg.msg != '<CORRUPTED>' and self.request_num == seg.sequence_num:
            self.send_to_app(seg.msg)
            self.send_to_network(Segment('ACK', 'sender', self.request_num))
            self.request_num += 1

        # If message is corrupted or unmatched sequence number
        # Ask the Sender to resend the previous packet
        else:
            print('request {}, seg {}'.format(self.request_num, seg.sequence_num))
            self.send_to_network(Segment('ACK', 'sender', self.request_num - 1))
