# AI-Container Instruction  

## Source Code is Located at /home/ubuntu/jack/LLM_Container AWS EC2 Server, the docker image is named as "my-ai-container"  

## 1. Brief
This container offers a packagable docker image file which includes a complete AI-Service tool module including:  

- **Dockerfile**：Docker Image Construction File  
- **requirements.txt**：Third party dependency python scripts  
- **start_services.sh**：bash script to start the docker image   
- **service_controller.py**：Main service script that makes use of the Qwen and Yolo model folders  
- **llm_models/**  
  - `Qwen3.0/`：Qwen3.0 model and its tool box    
  - `Yolov11/`：Yolov11 model and its tool box    
- **logs/**：Contains execution logs and errors   
- **configs/**  
  - `Config_qwen.yaml`：Qwen3.0 configuration files    
  
  **Note: if there is a conflict error when running the docker image, it is possible that this image container is already running, and thus please docker rm my-ai-container and then start the image again  

---

## 2. File Structure  

Container Structure    

![Structure 1](images/2.png)  

qwen weights structure    

![structure 2](images/1.png)

---

## 3. Configurations  

1. **weights path**  
   - local path：`/home/ubuntu/jack/qwen3_lora_merged`  
   - container path：`/app/qwen_llm/qwen3_lora_merged`  
   - if path changes are required, only change the local path but keep the container path unchanged  

2. **port forwarding**  
   - Uses port forwarding to link the host's port 5000 to the container port 5000  

---

## 4. Command Instructions for Starting up the Container  

### 1. Start up the container on server

```bash
docker run --gpus all 
  -p 5000:5000 
  -v /home/ubuntu/jack/qwen3_lora_merged:/app/qwen_llm/qwen3_lora_merged 
  --name my-ai-container 
  my-ai-container dispatch

"/home/ubuntu/jack/qwen3_lora_merged" this is the qwen weights path under the ec2 server, the weights are huge thus it is externally linked to a folder inside the container   
“/app/qwen_llm/qwen3_lora_merged” keep this unchanged!!!  
“my-ai-container” This is the container name  
“dispatch” This is the main command that starts the core service start_services.sh of the entire AI-Image  


### 2. Test on local machine "words based test"  
curl -X POST 
  http://<SERVER_IP>:5000/predict 
  -H "Content-Type: application/json" 
  -d '{"question": "What is the minimal value of y=5*x^2 + 7x + 75"}'  
<SERVER_IP>：Replace it with your own server IP or company server IP  
question Ask question using the prompt question:   

### 3. Test on local machine "Image based test" return Json format answer
curl -X POST 
  -F "image=@your_image.jpg" 
  http://<SERVER_IP>:5000/predict  
upload your_image.jpg，Local terminal will return time stamp, confidence score and other information 

### 4. Test on local machine "Image based test" return model processed image
curl -X POST 
  -F "image=@your_image.jpg" 
  http://<SERVER_IP>:5000/image 
  --output annotated_result.jpg  
upload your_image.jpg，return a processed imnage called annotated_results.jpg which is processed by the yolo model

### 5. bonus other command shell prompts please refer to start_services.sh 
    qwen bonus:    
    the model in this container includes data_prep.py, model_setup.py, and train.py, it is allowed to train and deploy your own model inside the container but not recommended if the weights are too big  
  
    Yolov11 bonus:  
    There are instructions allowed to ask the yolo model to recognize and process GIS images and store information into a sql data base  