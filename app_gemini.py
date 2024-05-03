import json
import os
import google.generativeai as genai
import subprocess
import shutil
import cv2

GOOGLE_API_KEY = "AIzaSyDWd4EHRMsEBWpf-K46GxNPpPdl_6nEIE0"
genai.configure(api_key=GOOGLE_API_KEY)




##GOOGLE MODEL LOADING
model = genai.GenerativeModel("gemini-1.5-pro-latest", generation_config={"response_mime_type": "application/json"})

FRAME_EXTRACTION_DIRECTORY = "/content/frames"
FRAME_PREFIX = "_frame"
def create_frame_output_dir(output_dir):
  if not os.path.exists(output_dir):
    os.makedirs(output_dir)
  else:
    shutil.rmtree(output_dir)
    os.makedirs(output_dir)

def extract_frame_from_video(video_file_path):
  print(f"Extracting {video_file_path} at 1 frame per second. This might take a bit...")
  create_frame_output_dir(FRAME_EXTRACTION_DIRECTORY)
  vidcap = cv2.VideoCapture(video_file_path)
  fps = vidcap.get(cv2.CAP_PROP_FPS)
  frame_duration = 1 / fps  # Time interval between frames (in seconds)
  output_file_prefix = os.path.basename(video_file_path).replace('.', '_')
  frame_count = 0
  count = 0
  while vidcap.isOpened():
      success, frame = vidcap.read()
      if not success: # End of video
          break
      if int(count / fps) == frame_count: # Extract a frame every second
          min = frame_count // 60
          sec = frame_count % 60
          time_string = f"{min:02d}:{sec:02d}"
          image_name = f"{output_file_prefix}{FRAME_PREFIX}{time_string}.jpg"
          output_filename = os.path.join(FRAME_EXTRACTION_DIRECTORY, image_name)
          cv2.imwrite(output_filename, frame)
          frame_count += 1
      count += 1
  vidcap.release() # Release the capture object\n",
  print(f"Completed video frame extraction!\n\nExtracted: {frame_count} frames")
  
class File:
  def __init__(self, file_path: str, display_name: str = None):
    self.file_path = file_path
    if display_name:
      self.display_name = display_name
    self.timestamp = get_timestamp(file_path)

  def set_file_response(self, response):
    self.response = response

def get_timestamp(filename):
  """Extracts the frame count (as an integer) from a filename with the format
     'output_file_prefix_frame00:00.jpg'.
  """
  parts = filename.split(FRAME_PREFIX)
  if len(parts) != 2:
      return None  # Indicates the filename might be incorrectly formatted
  return parts[1].split('.')[0]
  
# Make GenerateContent request with the structure described above.
def make_request(prompt, files):
  request_1 = [prompt]
  for file in files:
    request_1.append(file.timestamp)
    request_1.append(file.response)
  return request_1


##FUNCTION USING GOOGLE FROM HERE
#GOOGLE FIR TO SECTIONS
def FIR_to_sections(FIR):
  prompt = """Go through the FIR content and mention right sections of law to be invoked. Return the output in JSON schema :
  {"Sections of law":{"details":[{"section":,"description":}]}}
  """+ FIR
  
  response = model.generate_content(prompt)
  
  final_out = []
  res = json.loads(response.text)
  res_list = len(res['Sections of law']["details"])
  for i in range(0,res_list):
    string_out = res['Sections of law']["details"][i]['section']+" "+res['Sections of law']["details"][i]['description']
    final_out.append(string_out)
  
  return (final_out)



#FIR TO MISSING
def FIR_to_missing(FIR):

  prompt = """Go through the FIR content and mention right sections of law to be invoked. Return the output in JSON schema :
  {"Sections of law":{"details":[{"section":,"description":}]}}
  """+ FIR
  
  response = model.generate_content(prompt)
  res = json.loads(response.text)
  
  res_list = (res['Gaps Found'])
  return res_list
  


def FIR_to_all(FIR):


  prompt = """Go through the FIR content and mention right sections of law to be invoked, identify the gaps in the information provided and suggest all possible evidences to be collected to aid the investigating officer. Return the output in json format = {"Sections of law":{"details":[{"section":,"description":}]},"Gaps Found":{"details":[<list of strings>]},"Evidences to be collected":{"details":[<list of strings]}} \n"""+ FIR
  model = genai.GenerativeModel("gemini-1.5-pro-latest",
                                generation_config={"response_mime_type": "application/json"})
  response = model.generate_content(prompt)
  
  res = json.loads(response.text)
  print(res)
  
  return res

# Function to encode the image
def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')
 


def video_Analyzer(videopath):
    
    
    
    video_file_name = videopath
    extract_frame_from_video(video_file_name)
    # Process each frame in the output directory
    files = os.listdir(FRAME_EXTRACTION_DIRECTORY)
    files = sorted(files)
    files_to_upload = []
    for file in files:
      files_to_upload.append(
          File(file_path=os.path.join(FRAME_EXTRACTION_DIRECTORY, file)))
    
    # Upload the files to the API
    # Only upload a 10 second slice of files to reduce upload time.
    # Change full_video to True to upload the whole video.
    full_video = True
    
    uploaded_files = []
    print(f'Uploading {len(files_to_upload) if full_video else 10} files. This might take a bit...')
    
    for file in files_to_upload if full_video else files_to_upload[40:50]:
      print(f'Uploading: {file.file_path}...')
      response = genai.upload_file(path=file.file_path)
      file.set_file_response(response)
      uploaded_files.append(file)
    
    print(f"Completed file uploads!\n\nUploaded: {len(uploaded_files)} files")
    
    # Create the prompt.
    prompt = """This is the video taken by Investigating Officer of the incident. Please go through the FIR, analyze and relate this video to the incident which will help the Investigating Officer. Please do not describe the FIR again, directly try to link the video and FIR, Also highlight the keywords for Investigating officer from the description. Return the output in json format = {"Description":[],"Keywords":[]} . FIR content: """+ session['FIR_content']
    
    # Make the LLM request.
    request_2 = make_request(prompt, uploaded_files)
    response = model.generate_content(request_2,
                                      request_options={"timeout": 600}, generation_config = {
        'response_mime_type': 'application/json'  # Add this line for JSON response
    })
    
    
    res = json.loads(response.text)
    print(res['Description'])
    #AI_evidence_out = Evidence_image_analysis("image_data/"+file_data.filename, session['FIR_content'])
    
    
    return res['Description']
    


def video_process(video_path):

    file = request.files["video_file"]
    
    
    filename_vd = video_path
  
    p = subprocess.Popen(['ffmpeg',"-i", filename_vd,"-ac",'1',"-ar",'16000',"-vn","-acodec","pcm_s16le",filename], stdout = subprocess.PIPE)
    (output, err) = p.communicate()
    p_status = p.wait()
    
 
    
    your_file = genai.upload_file(path=filename)

    # Configure JSON response and safety settings
    generation_config = {
        'response_mime_type': 'application/json'  # Add this line for JSON response
    }
    
    prompt = 'Listen carefully to the following audio file. Provide the transcription in plain text, try to differentiate speaker, one is Investigating Officer and one more is the Witness. Return the response in dictionary format in this way {"Transcription": <String>}'
    model = genai.GenerativeModel('models/gemini-1.5-pro-latest')
    
    response = model.generate_content([prompt, your_file], generation_config=generation_config)
    
    print(response)
    res = json.loads(response.text)
    print(res)
    if isinstance(res,list):
      res = res[0]
      transcript = res['Transcription']
    else:
      transcript = res['Transcription']
      
    your_file = genai.upload_file(path=filename)

    # Configure JSON response and safety settings
    generation_config = {
        'response_mime_type': 'application/json'  # Add this line for JSON response
    }
    
    prompt = 'Listen carefully to the following audio file. try to differentiate speaker, one is Investigating Officer and one more is the Witness, Provide the emotional state of the witness through his voice, also try to highlight any important things observed in his voice. Return the response in JSON format in this way {"Voice analysis": <String>}'
    #model = genai.GenerativeModel('models/gemini-1.5-pro-latest')
    
    response = model.generate_content([prompt, your_file], generation_config=generation_config)
    
    print(response)
    res = json.loads(response.text)
    print(res)
    
    voice_analysis = res["Voice analysis"]
    
    video_file_name = filename_vd
    extract_frame_from_video(video_file_name)
    # Process each frame in the output directory
    files = os.listdir(FRAME_EXTRACTION_DIRECTORY)
    files = sorted(files)
    files_to_upload = []
    for file in files:
      files_to_upload.append(
          File(file_path=os.path.join(FRAME_EXTRACTION_DIRECTORY, file)))
    
    # Upload the files to the API
    # Only upload a 10 second slice of files to reduce upload time.
    # Change full_video to True to upload the whole video.
    full_video = True
    
    uploaded_files = []
    print(f'Uploading {len(files_to_upload) if full_video else 10} files. This might take a bit...')
    
    for file in files_to_upload if full_video else files_to_upload[40:50]:
      print(f'Uploading: {file.file_path}...')
      response = genai.upload_file(path=file.file_path)
      file.set_file_response(response)
      uploaded_files.append(file)
    
    print(f"Completed file uploads!\n\nUploaded: {len(uploaded_files)} files")
    
    # Create the prompt.
    prompt = """This is the video taken by Investigating Officer when the witness was giving his / her statement. Please go through the video and give comments on the Facial Expressions and try to give some feedback on the same. Return the output in json format = {"Video_Analysis":<String>} . """
    
    # Make the LLM request.
    request_2 = make_request(prompt, uploaded_files)
    response = model.generate_content(request_2,
                                      request_options={"timeout": 600}, generation_config = {
        'response_mime_type': 'application/json'  # Add this line for JSON response
    })
    
    
    res = json.loads(response.text)
    print(res)
       
    
            
    
    
    return {"message":"success","transcription": transcript, 'video_analysis':res["Video_Analysis"], 'audio_analysis': voice_analysis }
    

