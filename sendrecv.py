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

class Segment:
    def __init__(self, msg, dst, alt_bit):
        self.msg = msg
        self.dst = dst
        self.alt_bit = alt_bit

class NaiveSender(BaseSender):
    def __init__(self, app_interval):
        super(NaiveSender, self).__init__(app_interval)

    def receive_from_app(self, msg):
        seg = Segment(msg, 'receiver')
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
        seg = Segment(msg, 'receiver', self.alt_bit)
        self.send_to_network(seg)
        self.start_timer(self.app_interval)
        self.cur_seg = seg
        self.disallow_app_msgs()

    def receive_from_network(self, seg):
        if seg.msg == 'ACK' and self.alt_bit == seg.alt_bit:
            self.alt_bit = not self.alt_bit
            self.end_timer()
            self.allow_app_msgs()

        if seg.msg == 'ACK' and self.alt_bit != seg.alt_bit:
            self.send_to_network(Segment('ACK', 'receiver', self.alt_bit))
            self.start_timer(self.app_interval)

        if seg.msg == '<CORRUPTED>':
            self.send_to_network(Segment('ACK', 'receiver', self.alt_bit))
            self.start_timer(self.app_interval)

    def on_interrupt(self):
        self.start_timer(self.app_interval)
        self.send_to_network(self.cur_seg)


class AltReceiver(BaseReceiver):
    def __init__(self):
        super(AltReceiver, self).__init__()
        self.alt_bit = True

    def receive_from_client(self, seg):
        if seg.msg == '<CORRUPTED>':
            self.send_to_network(Segment('ACK', 'sender', not self.alt_bit))

        if self.alt_bit == seg.alt_bit:
            self.send_to_app(seg.msg)
            self.send_to_network(Segment('ACK', 'sender', self.alt_bit))
            self.alt_bit = not self.alt_bit
        else:
            self.send_to_network(Segment('ACK', 'sender', not self.alt_bit))


class GBNSender(BaseSender):
    # TODO: fill me in!
    pass

class GBNReceiver(BaseReceiver):
    # TODO: fill me in!
    pass
