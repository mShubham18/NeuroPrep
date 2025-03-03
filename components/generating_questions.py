from components.model_configuration import model_config
import markdown

def generate_Introduction(metrics_dict:dict)->list:
    prompt = f"""I am creating a web app platform that fetches user resumes and provides a mock interview consisting of Aptitude & Reasoning, Technical, and HR rounds. I have some detailed metrics that can be used to create question content for the exam.

    I'll be providing the metrics to you in the form of dictionary The metrics contain the information that you could use to create the question like difficulty, skills and all. it consits of many other metrics too so only use those metrics that are needed for questions related to Introduction. round. as I have total 4 rounds like: Introduction, Aptitude, Technical,Coding, and Hr round
    what i need in return is a list of 5-7 Introduction round questions, comma seperated and seprated by "||". they should be basically to greet the user, make him comfortable and prepared for the exam.
    The name of the job seeker is ramesh.
    start with greeting like hello how are you
    Always assume this is a real interview so dont talk about things like how do you like this mock interview
    since this is just a introduction round, do not talk about deeep technical stuff as it will later on be explain

    do not include any unncessary clutter like explaination and salutation
    keep the questions progessive asumming you have got your respinse to the qeustions

    {metrics_dict}"""
    model = model_config()
    response = model.generate_content(prompt)
    questions_list = (response.text).split("||")
    questions_list = [question.replace("\n","") for question in questions_list]
    return questions_list

def generate_Aptitude(metrics_dict:dict)->dict:
    prompt = f"""You are an AI generating MCQ-based aptitude questions for a mock interview exam.  

    **Instructions:**  
    - Use only the provided **metrics** to create **30 MCQ aptitude questions**.  
    - Format the output **exactly** as shown below, with `||` separating each question.  
    - Each question **must** follow this structure:  
      **Question text // option1, option2, option3, option4**  
    - No explanations, no extra text, just the formatted questions.  

    **Example Output:**  
    What is 2+2? // 1, 2, 3, 4 || What is the capital of France? // Berlin, Madrid, Paris, Rome  

    **Metrics for generating questions:**  
    {metrics_dict}  

    **Output the questions now:**"""
    model = model_config()
    response = model.generate_content(prompt)
    questions = (response.text).split("||")
    aptitude_questions_dict = {}
    for line in questions:
        question_list = line.split("//")
        question= question_list[0]
        mcq= question_list[1]
        mcq_list = mcq.split(",")
        aptitude_questions_dict[question]=mcq_list

    return aptitude_questions_dict

def generate_Technical(metrics_dict:dict)->dict:
    prompt = f"""You are an AI assistant generating **30 multiple-choice questions (MCQs)** for a **mock technical interview**.

    ### **Important Instructions:**
    - Only generate questions related to **System Design, OS, DBMS, and Computer Networks**.
    - **Strictly follow the output format** with **no extra explanations, no numbering, and no missing values**.
    - Each question **must have exactly four answer options**.
    - Separate each question using `||` (double pipe).
    - Use `//` (double forward slashes) to separate the question text from the answer choices.
    - **The first option should always be the correct answer** (but do not indicate this explicitly).

    ---

    ### **Output Format Example:**
    What is the primary key in a database? // A unique identifier, A duplicate record, A null value, A foreign key ||
    What does an operating system do? // Manages hardware, Compiles code, Runs JavaScript, Controls database records
    ### **Here are the question generation metrics:**
    {metrics_dict}
    Now, generate exactly **30 MCQs** following the format strictly. Ensure all questions and answers are complete and correctly formatted."""
    model = model_config()
    response = model.generate_content(prompt)
    questions = (response.text).split("||")
    technical_questions_dict = {}
    for line in questions:
        question_list = line.split("//")
        question= question_list[0]
        mcq= question_list[1]
        mcq_list = mcq.split(",")
        technical_questions_dict[question]=mcq_list

    return technical_questions_dict


def generate_Coding(metrics_dict:dict)->str:
    prompt = f"""I am creating a web app platform that fetches user resumes and provides a mock interview consisting of Aptitude & Reasoning, Technical, and HR rounds. I have some detailed metrics that can be used to create question content for the exam.

    I'll be providing the metrics to you in the form of dictionary The metrics contain the information that you could use to create the question like difficulty, skills and all. it consits of many other metrics too so only use those metrics that are needed for questions related to aptitude as i'll be seprately creating for other techniacla rounds.
    what i need in return is A codig question in leetcode format like how a leetcode question is in the format of a Markdown format. It should contain each and everthing

    Keep in mind the question should be unique and free from copyrighted material or must have noticelably name and value changes
    Since this question is for examinee, it should not reveal any other info just statement, description and other things no comments like in the brakcerts etc.
    metrics dictionary: 
    {metrics_dict}"""
    model = model_config()
    response = model.generate_content(prompt)
    markdown_text = response.text
    html_content = markdown.markdown(markdown_text)

    return html_content

def generate_HR(metrics_dict:dict)->list:
    prompt = f"""I am creating a web app platform that fetches user resumes and provides a mock interview consisting of Aptitude & Reasoning, Technical, and HR rounds. I have some detailed metrics that can be used to create question content for the exam.

    I'll be providing the metrics to you in the form of dictionary The metrics contain the information that you could use to create the question like difficulty, skills and all. it consits of many other metrics too so only use those metrics that are needed for questions related to HR round. as i'll be seprately creating for other techniacla rounds.
    what i need in return is a list of 5-10 HR round questions, more the difficulty more is the num of questions , seprated by comma and divided by "||"

    do not include any unncessary clutter like explaination and salutation
    metrics dictionary: 
    {metrics_dict}"""
    model = model_config()
    response = model.generate_content(prompt)
    questions_list = response.text
    questions_list=questions_list.split("||")
    questions_list = [question.replace("\n","") for question in questions_list]

    return questions_list