import base64
import binascii

def deserialize(string, length):
    """
    Given a string and its expected length, try a variety of encodings to get
    it back into its original format.

    Expected input formats include base64/base32 and binascii. The idea is to
    go from wire-safe/readable formats to raw bytes.
    """

    if len(string) == length:
        return string
    elif len(string) == length * 2:
        # Hexlified?
        try:
            return binascii.unhexlify(string)
        except TypeError:
            return base64.b32decode(string)
    elif len(string) / 8 == (length + 4) // 5:
        return base64.b32decode(string)
    else:
        raise ValueError, "Couldn't guess how to deserialize %s" % string
