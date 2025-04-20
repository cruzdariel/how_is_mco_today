def post(caption, platform=None, image=None):
    if platform is None:
        return ValueError("No platform specified!")

    if platform not in ["BSKY", "X"]:
        return ValueError("I can only post on BSKY and X.")
    
    BSKY_USERNAME = os.getenv("BSKY_USERNAME")
    BSKY_PASSWORD = os.getenv("BSKY_PASSWORD")

    if platform=="BSKY":
        client = Client()
        client.login(BSKY_USERNAME, BSKY_PASSWORD)

        message1, message2, message3 = caption

        if image is not None:
            try:
                with open('images/generated_image.jpg', 'rb') as f:
                    img_data = f.read()

                    response1 = client.send_image(text=message1, image=img_data, image_alt='Status image')
                    root_ref = models.create_strong_ref(response1)
                    print("Posted thread 1/3 with image!")

                    response2 = client.send_post(message2,
                        reply_to=models.AppBskyFeedPost.ReplyRef(
                            parent=models.create_strong_ref(response1),
                            root=root_ref))
                    print("Posted thread 2/3!")

                    response2 = client.send_post(message3,
                        reply_to=models.AppBskyFeedPost.ReplyRef(
                            parent=models.create_strong_ref(response2),
                            root=root_ref))
                    print("Posted thread 3/3!")
            except Exception as e:
                print(f"Error: {e}")

        if image is None:
            try:
                client.send_post(caption)
                print("Posted without image")
            except Exception as e:
                print(f"Error: {e}")
    
    if platform=="X":
        X_API_KEY = os.getenv("X_API_KEY")
        X_API_SECRET = os.getenv("X_API_SECRET")
        return