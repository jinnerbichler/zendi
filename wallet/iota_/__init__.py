class NotEnoughBalanceException(Exception):
    def __init__(self, *args, user, proposed_amount, balance):
        self.user = user
        self.proposed_amount = proposed_amount
        self.balance = balance
        message = '{} has not enough balance ({}) for sending {} IOTA'.format(user, balance, proposed_amount)
        super().__init__(message, *args)


def trytes2string(trytes):
    return str(trytes)


def string2trytes_bytes(string):
    return string.encode('utf-8')
