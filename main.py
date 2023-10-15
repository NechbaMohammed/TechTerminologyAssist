from website  import create_app
from website.utils import *
app = create_app()
if __name__ == '__main__':
    app.run(debug=True)
