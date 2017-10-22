class NotEnoughBalanceException(Exception):
    def __init__(self, *args, user, proposed_amount, balance):
        self.user = user
        self.proposed_amount = proposed_amount
        self.balance = balance
        message = '{} has not enough balance ({}) for sending {} IOTA'.format(user, balance, proposed_amount)
        super().__init__(message, *args)
