# noinspection PyUnresolvedReferences
from wallet.iota_.iota_api import IotaApi
from wallet.models import IotaAddress
from wallet.user_utils import get_user_safe


# noinspection PyUnresolvedReferences
def get_new_address(user):
    """
    Creates a new IOTA address, which is not attached to the tangle.
    :param user: user object containing seed
    :return: new address in the IOTA network (not attached to the Tangle)
    """
    api = IotaApi(seed=user.iota_seed)

    # create and store new address
    new_address = api.get_new_address()
    IotaAddress.objects.get_or_create(user=user, address=new_address)

    return new_address


def send_iota(sender, receiver, amount, message):
    # get proper users
    _, sending_user = get_user_safe(email=sender)
    is_new, receiving_user = get_user_safe(email=receiver)

    # ToDo: inform user about new wallet

    api = IotaApi(seed=sending_user.iotaseed.seed)

    return
