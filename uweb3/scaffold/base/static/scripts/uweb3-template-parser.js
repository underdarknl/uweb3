class Template {
  FUNCTION = /\{\{\s*(.*?)\s*\}\}/mg;
  tag = /(\[\w+(?:(?::[\w-]+)+)?(?:(?:\|[\w-]+(?:\([^()]*?\))?)+)?\])/gm;

  constructor(template, replacements){
    this.template = template;
    this.html = []
    this.replacements = replacements;
    this.parse()
    this.replacePlaceholders();
  }

  replacePlaceholders(){
    this.html.map((value) => {
      if(value instanceof TemplateText){
        for(let placeholder in this.replacements){
          value.value = value.value.split(placeholder).join(this.replacements[placeholder]);
        }
      }
    });
    this.template = "";
    this.html.map((value) => {
      this.template += value.value;
    });
  }   

  parse(){
    let m;
    let matches = []
    let i = 0;
    while ((m = this.FUNCTION.exec(this.template)) !== null) { 
      m.forEach((match, groupIndex) => {
        if(groupIndex == 0){
          let index;
          if(i % 2 == 0){
            index = m.index;
          }else{
            index = this.FUNCTION.lastIndex;
          }
          matches.push(index);
          i++;
        }
      });
    }

    for(let i = 0; i < matches.length; i += 2){
      if(i == 0){
        let value = this.template.substring(0, matches[i])
        //If there is no templatefunction on the start of the file add templatetext
        if(value.length > 1){
          this.html.push(new TemplateText(this.template.substring(0, matches[0])))
        }
        this.html.push(new TemplateFunction(this.template.substring(matches[i], matches[i + 1])))
      }else{
        this.html.push(new TemplateFunction(this.template.substring(matches[i], matches[i + 1])))

      }
      if(i !== matches.length / 2){
        this.html.push(new TemplateText(this.template.substring(matches[i + 1], matches[i + 2])))
      }else{
        this.html.push(new TemplateText(this.template.substring(matches[i + 1], this.template.length)))
      }
    }
  }
}

class TemplateText {
  constructor(value){
    this.value = value;
  }
}

class TemplateFunction {
  constructor(value){
    this.value = value;
  }
}

