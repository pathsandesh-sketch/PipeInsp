import cv2

class Display:
    def show(self, frame):
        cv2.imshow("Live Feed", frame)
        return cv2.waitKey(1)

    def close(self):
        cv2.destroyAllWindows()
