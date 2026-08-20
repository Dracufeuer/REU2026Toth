from oned.spanner import oned_loop
from twod.spanner import twod_loop


def main():
    while True:
        user_input = input("Enter 1 for 1D or 2 for 2D (n to exit): ")
        if user_input == "1":
            oned_loop()
            break
        elif user_input == "2":
            twod_loop()
            break

        else: break

    print("program terminated")




if __name__ == "__main__":
    main()