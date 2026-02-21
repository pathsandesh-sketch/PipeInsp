from receiver import Receiver
from display import Display

def main():
    receiver = Receiver()
    display = Display()

    try:
        while True:
            frame = receiver.receive_frame()
            key = display.show(frame)

            if key == 27:  # ESC key
                break

    except KeyboardInterrupt:
        print("Stopping receiver...")

    finally:
        display.close()

if __name__ == "__main__":
    main()
