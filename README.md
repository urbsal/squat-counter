 ####  Source Code and SetUp Instruction

 The source code for the Exercise Rep counter application is written in Python. To developed this application python 3.11.9 version was used. All the required libraries for the application were installed in Python virtual environment (venv). 

To set up the application, first create a separate folder for the project using the following command:
 mkdir <folder_name>

 Navigate into the newly created folder:
 cd <folder_name>

 Create a virtual environment inside the project folder using: 
 Python -m venv venv

 once the virtual environment is created activate it with command:
 venv\Scripts\activate

 venv will appear in terminal line which means python and pip now use this environment

 pip install -r requirements.txt
 This install the required dependencies in the project's virtual environment. 

### Model, Library, API 

In the application MediaPipe Pose Library developed by Google was used. The application uses MediaPipe Pose Solution API(mp.solution.pose), which is based on BlazePose pose estimation model. 
The model detect 33 body landmarks. In our application landmark 23, 25 and 27 were used for squat detection to calculate the knee angle. Each landmark provides normalized x and y cordinates and visibility score.  

The application counts squats. 

Landmark 23, 25 and 27 were used. 

The application detect  two movement phases:UP and DOWN. When the angel of the knee is 100 or less than 100 degree it is classified as Down Phase. When the angle reach 155 or more it is classified as UP phase. These threshold values can be adjusted according to user's requirements. 

UP - DOWN - UP: One full squat is counted as one repetition. 

To counted as Down : knee angle should be 100° or less 
To counted as UP : knee angel should be 155° or more
Moving average technique for smoothing the angel. The average of the latest 3 angels values is used. 

Videos work well when the camera can see the body clearly, with at least half of the body visible. The person should perform the squats slowly and clearly, because very fast movements can make it harder for MediaPipe to track the body landmarks correctly.

Videos are difficult when the body is not fully visible, the camera is too far away, or the person moves to fast. Videos with poor lighting or when the body is blocked can also make it difficult for MediaPipe to track the body landmarks.  

During testing, own computer camera and own video was used and no other's people information was involved.The camera and videos should be used in a safe and private environment. The application is for counting exercises and should not be used as medical or fitness advices. 

