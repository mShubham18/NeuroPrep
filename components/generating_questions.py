from components.model_configuration import model_config
import markdown
def generate_Aptitude(metrics_dict:dict)->dict:
    prompt = f"""I am creating a web app platform that fetches user resumes and provides a mock interview consisting of Aptitude & Reasoning, Technical, and HR rounds. I have some detailed metrics that can be used to create question content for the exam.

    I'll be providing the metrics to you in the form of dictionary The metrics contain the information that you could use to create the question like difficulty, skills and all. it consits of many other metrics too so only use those metrics that are needed for questions related to aptitude as i'll be seprately creating for other techniacla rounds.
    what i need in return is A list of 30 mcq based "aptitude" questions that are in the form of this
    what is x~ option1,option2,option3,option4
    it should be a list of comma seperated qustions seperated by || to differentiate. 
    here is the dictionary. do not give salutations just output

    {metrics_dict}"""
    model = model_config()
    response = model.generate_content(prompt)
    questions = (response.text).split("||")
    aptitude_questions_dict = {}
    for line in questions:
        question = line.split("~")[0]
        mcq_list= line.split("~")[1]
        mcq_list = mcq_list.split(",")
        aptitude_questions_dict[question]=mcq_list

    return aptitude_questions_dict

def generate_Technical(metrics_dict:dict)->dict:
    prompt = f"""I am creating a web app platform that fetches user resumes and provides a mock interview consisting of Aptitude & Reasoning, Technical, and HR rounds. I have some detailed metrics that can be used to create question content for the exam.

    I'll be providing the metrics to you in the form of dictionary The metrics contain the information that you could use to create the question like difficulty, skills and all. it consits of many other metrics too so only use those metrics that are needed for questions related to technical as i'll be seprately creating for other rounds.
    what i need in return is A list of 30 mcq based "System design,OS,DBMS,ComputerNetwork" questions that are in the form of this
    what is x~ option1,option2,option3,option4
    it should be a list of comma seperated qustions seperated by || to differentiate. 
    here is the dictionary. do not give salutations just output

    {metrics_dict}"""
    model = model_config()
    response = model.generate_content(prompt)
    questions = (response.text).split("||")
    aptitude_questions_dict = {}
    for line in questions:
        question = line.split("~")[0]
        mcq_list= line.split("~")[1]
        mcq_list = mcq_list.split(",")
        aptitude_questions_dict[question]=mcq_list

    return aptitude_questions_dict

def generate_Technical(metrics_dict:dict)->dict:
    prompt = f"""I am creating a web app platform that fetches user resumes and provides a mock interview consisting of Aptitude & Reasoning, Technical, and HR rounds. I have some detailed metrics that can be used to create question content for the exam.

    I'll be providing the metrics to you in the form of dictionary The metrics contain the information that you could use to create the question like difficulty, skills and all. it consits of many other metrics too so only use those metrics that are needed for questions related to technical as i'll be seprately creating for other rounds.
    what i need in return is A list of 30 mcq based "System design,OS,DBMS,ComputerNetwork" questions that are in the form of this
    what is x~ option1,option2,option3,option4
    it should be a list of comma seperated qustions seperated by || to differentiate. 
    here is the dictionary. do not give salutations just output

    {metrics_dict}"""
    model = model_config()
    response = model.generate_content(prompt)
    questions = (response.text).split("||")
    aptitude_questions_dict = {}
    for line in questions:
        question = line.split("~")[0]
        mcq_list= line.split("~")[1]
        mcq_list = mcq_list.split(",")
        aptitude_questions_dict[question]=mcq_list

    return aptitude_questions_dict

def generate_Coding(metrics_dict:dict)->str:
    prompt = f"""I am creating a web app platform that fetches user resumes and provides a mock interview consisting of Aptitude & Reasoning, Technical, and HR rounds. I have some detailed metrics that can be used to create question content for the exam.

    I'll be providing the metrics to you in the form of dictionary The metrics contain the information that you could use to create the question like difficulty, skills and all. it consits of many other metrics too so only use those metrics that are needed for questions related to aptitude as i'll be seprately creating for other techniacla rounds.
    what i need in return is A codig question in leetcode format like how a leetcode question is in the format of a Markdown format. It should contain each and everthing

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