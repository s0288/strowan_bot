from clarifai.rest import ClarifaiApp
import config

app = ClarifaiApp(api_key=config.CLARIFY)

# get the general model
model = app.models.get("general-v1.3")

# predict with the model
model.predict_by_url(url='https://samples.clarifai.com/metro-north.jpg')
