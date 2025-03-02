from components.model_configuration import model_config
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

    I'll be providing the metrics to you in the form of dictionary The metrics contain the information that you could use to create the question like difficulty, skills and all. it consits of many other metrics too so only use those metrics that are needed for questions related to aptitude as i'll be seprately creating for other techniacla rounds.
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

