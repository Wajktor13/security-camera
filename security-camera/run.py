import cv2

def show_video():
    cap = cv2.VideoCapture(0)

    if cap.isOpened() == False:
        print("Error opening video file")

    while cap.isOpened():

        ret, frame = cap.read()
        if ret:
            cv2.imshow('Frame', frame)

            if cv2.waitKey(25) & 0xFF == ord('q'):
                break
        else:
            break

    cap.release()

    cv2.destroyAllWindows()


if __name__ == "__main__":
    show_video()
