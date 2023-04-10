import board
import busio
import usb_hid
from adafruit_hid.keyboard import Keyboard
from key_decode_dict import KEY_DECODE_DICT

# Global variables
BYTES_PER_READ = 32 # number of bytes read in from UART
HOLD_KEYS_MODIFER = '~'
CLEAR_BUFFER_MODIFER = '!'
SEPARATE_KEYS_MODIFER = '|'

# Setup
uart = busio.UART(board.TX, board.RX, baudrate=115200)
kbd = Keyboard(usb_hid.devices)

def print_uart(obj):
    uart.write(bytes(str(obj), 'ascii') + '\r\n')

def bytes_to_str(byte_string):
    return ''.join([chr(b) for b in byte_string])
  
def convert_string_to_key(key_string):
    """Use the dict to return the corresponding keycode for a symbol
    If the keycode is not recognized, print a warning string and return None.
    
    Args:
        key_string: A string representing the desired key
    
    Returns:
        None, or Keycode object
    """
    try:
        key = KEY_DECODE_DICT[key_string]
    except:
        key = None

    if (key is None):
        print_uart('Unsupported symbol: {}'.format(key_string))
    return key
  
def parse_raw_uart(byte_string):
    """Parse a string of bytes from the uart
    
    Args:
        byte_string: The raw byte string to parse
    
    Returns: A tuple of the form (bool, list)
        bool: True, if the keys are to be held. False otherwise.
        list: A list of Keycode objects found in the bytestring
    """
    char_string = bytes_to_str(byte_string).upper().strip()
    if len(char_string) == 0:
        return False, []
    print_uart(f'string {char_string}')
    hold_keys = False # Assume the keys aren't held until told otherwise
    
    if char_string[0] == HOLD_KEYS_MODIFER:
        # If the first key is equal to HOLD_KEYS_MODIFER, hold the keys
        hold_keys = True
        char_string = char_string[1:] # Drop the modifer key

    raw_symbols = char_string.split(SEPARATE_KEYS_MODIFER)
    
    keycode_list = []
    for symbol in raw_symbols:
        key_obj = convert_string_to_key(symbol)
        if key_obj is not None:
            keycode_list.append(key_obj)
  
    return hold_keys, keycode_list
  
def keyboard_loop():
    """The main loop of the program
    
    Args:
        None
    Returns:
        None
    """
    byte_string = b''
    byte_string_updated = True
    while True:
        uart_bytes = uart.read(32)

        if byte_string != b'' and byte_string_updated:
            print_uart(f"Current buffer: {bytes_to_str(byte_string)}")
            byte_string_updated = False

        if uart_bytes is None:
            continue
        elif (b'\n' not in uart_bytes and b'\r' not in uart_bytes):
            print_uart(uart_bytes)
            byte_string = byte_string + uart_bytes
            byte_string_updated = True
            continue
        else:
            byte_string = byte_string + uart_bytes
            byte_string_updated = True
            print_uart(uart_bytes)
        
        print_uart(f"input: {byte_string}")
        hold_keys, keycode_list = parse_raw_uart(byte_string)
        byte_string = b''

        print_uart(keycode_list)
    
        if hold_keys:
            # Send the keys pressed, and left them held
            kbd.press(*keycode_list)
        else:
            # Send the keys, and then send a report that they were released
            kbd.send(*keycode_list)

print_uart("Starting loop")
keyboard_loop()