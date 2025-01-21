# Try out in repl
import dotenv
from gjk.config import Settings
from gjk.weather_service import WeatherService

dotenv.load_dotenv(dotenv.find_dotenv())

w = WeatherService(Settings())
w.start()
