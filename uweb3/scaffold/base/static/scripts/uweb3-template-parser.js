class Template {  
  get FUNCTION() {
    return /\{\{\s*(.*?)\s*\}\}/mg;
  }

  get TAG() {
    return /(\[\w+(?:(?::[\w-]+)+)?(?:(?:\|[\w-]+(?:\([^()]*?\))?)+)?\])/gm;
  }

  constructor(template, replacements){
    console.log(replacements);
    window.replacements = replacements;
    this.scopes = [];
    this.AddString(template);

    this.template = template;
    this.html = template;
    this.replacements = replacements;
    // this.html = []
    // this.parse()
    // this.replacePlaceholders();
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
  
  returnNeededPlaceholders(str){
    let tagsWithValues = {}
    str.match(this.TAG).map((tag) => {
      tagsWithValues[tag] = this.replacements[tag];
    });
    return tagsWithValues;
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
        if(value.length > 1){
          this.html.push(new TemplateText(this.template.substring(0, matches[0])))
        }
        this.html.push(new TemplateFunction(this.template.substring(matches[i], matches[i + 1]), 
        this.returnNeededPlaceholders(this.template.substring(matches[i], matches[i + 1]))));
      }else{
        this.html.push(new TemplateFunction(this.template.substring(matches[i], matches[i + 1]), 
        this.returnNeededPlaceholders(this.template.substring(matches[i], matches[i + 1]))));

      }
      if(i !== matches.length / 2){
        this.html.push(new TemplateText(this.template.substring(matches[i + 1], matches[i + 2])));
      }else{
        this.html.push(new TemplateText(this.template.substring(matches[i + 1], this.template.length)));
      }
    }
  }

  AddString(template) {
    let nodes = template.split(this.FUNCTION);
    nodes.map((node, index) => {
      if(index % 2){
        this._ExtendFunction(node);
      }else{
        this._ExtendText(node)
      }
    });
  }

  _ExtendFunction(nodes) {
    nodes = nodes.split(" ");
    let func = nodes.shift();
    func = func.charAt(0).toUpperCase() + func.substring(1);
    this[`_TemplateConstruct${func}`](nodes);
  }

  _AddToOpenScope(item){
    // this.scopes[this.scopes.length  - 1];
  }

  _StartScope(scope){
    this._AddToOpenScope(scope);
    this.scopes.push(scope);
  }

  _ExtendText(nodes){
  }

  _TemplateConstructIf(nodes){
    //Processing for {{ if }} template syntax
    this._StartScope(new TemplateConditional(nodes.join(' ')));
    console.log(this.scopes);
  }

  _TemplateConstructElse(){
    //Processing for {{ else }} template syntax.
    // this._VerifyOpenScope(TemplateConditional);
    // this.scopes[-1].Else();
  }

  _TemplateConstructEndif(){
    //Processing for {{ endif }} template syntax.
    // self._CloseScope(TemplateConditional)
  }
}

class TemplateConditional {
  constructor(expr) {
    this.branches = [];
    this.default = null;
    this.NewBranch(expr);
  }

  NewBranch(expr){
    console.log(window.replacements);
    this.branches.push([expr, []]);
  }
}

class TemplateText {
  constructor(value){
    this.value = value;
  }
}

class TemplateTag {
  get TAG() {
    return /(\[\w+(?:(?::[\w-]+)+)?(?:(?:\|[\w-]+(?:\([^()]*?\))?)+)?\])/gm;
  }

  constructor(tag){
    this.value = window.global_replacements[tag]    
  }

  static FromString(tag) {
    return new TemplateTag(tag);
  }
}


class TemplateLoop {

}
