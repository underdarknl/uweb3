class Template {  
  get FUNCTION() {
    return /\{\{\s*(.*?)\s*\}\}/mg;
  }

  get TAG() {
    return /(\[\w+(?:(?::[\w-]+)+)?(?:(?:\|[\w-]+(?:\([^()]*?\))?)+)?\])/gm;
  }

  constructor(template, replacements){
    window.replacements = replacements;
    this.tmp = {};
    this.scopes = [];
    this.AddString(template);
    this.template = "";

    for(let property in this.tmp){
      this.template += this.tmp[property].nodes;
    }
    for(let replacement in replacements){
      this.template = this.template.split(replacement).join(replacements[replacement]);
    }
  }


 
  
  returnNeededPlaceholders(str){
    let tagsWithValues = {}
    str.match(this.TAG).map((tag) => {
      tagsWithValues[tag] = this.replacements[tag];
    });
    return tagsWithValues;
  }

  AddString(template) {
    let nodes = template.split(this.FUNCTION);
    nodes.map((node, index) => {
      if(index % 2){
        this._ExtendFunction(node, index);
      }else{
        this._ExtendText(node, index)
      }
    });

    console.log("EVALUATING SCOPE");
    this._EvaluateScope();
  }
  _EvaluateScope(){
    this.scopes.map((object, index) => {
      let deleteScopes = false;
      for(let branch in object.branches){
        if(!object.branches[branch].istrue){
          //Delete all the scopes from which the condition was not met
          if(object.branches[branch].istrue !== undefined || deleteScopes){
            //If the branch returns undefined its the last clause in the if statement so it will always be true
            delete this.tmp[object.branches[branch].index + 1];
          }
        }else{
          deleteScopes = true;
        }
      }
    });
  }
  _ExtendFunction(nodes, index) {
    nodes = nodes.split(" ");
    let func = nodes.shift();
    func = func.charAt(0).toUpperCase() + func.substring(1);
    this[`_TemplateConstruct${func}`](nodes, index);
  }

  _AddToOpenScope(item){
    // this.scopes[this.scopes.length  - 1];
  }

  _StartScope(scope){
    // this._AddToOpenScope(scope);
    this.scopes.push(scope);
  }

  _ExtendText(nodes, index){
    this.tmp[index] = { nodes: nodes };
  }

  _TemplateConstructIf(nodes, index){
    //Processing for {{ if }} template syntax
    this._StartScope(new TemplateConditional(nodes.join(' '), index));
  }

  _TemplateConstructElse(nodes, index){
    //Processing for {{ else }} template syntax.
    // this._VerifyOpenScope(TemplateConditional);
    // this.scopes[-1].Else();
    this.scopes[this.scopes.length - 1] = this.scopes[this.scopes.length - 1].Else(index)
  }

  _TemplateConstructEndif(){
    //Processing for {{ endif }} template syntax.
    // self._CloseScope(TemplateConditional)
  }
}

class TemplateConditional {
  get TAG() {
    return /(\[\w+(?:(?::[\w-]+)+)?(?:(?:\|[\w-]+(?:\([^()]*?\))?)+)?\])/gm;
  }

  constructor(expr, index) {
    this.branches = [];
    this.default = null;
    this.NewBranch(expr, index);
  }

  NewBranch(expr, index){
    let temp_expr = ""
    let variables = ""
    
    if(expr.search(' in ') !== -1){
      throw "NotImplemented"
    }else{
      expr.match(this.TAG).map((value) => {
        //if the regex is a match it is a variable else its a variable function such as [variable|len]
        let regex = new RegExp(/(\[\w+?\])/gm);
        if(regex.test(value)){
          variables += `let ${value.substring(1, value.length - 1)} = "${window.replacements[value]}";`;
          temp_expr = expr.replace(value, value.substring(1, value.length - 1));
        }else{
          temp_expr = expr.replace(value, window.replacements[value]);
        }
      });
    }
    this.branches.push({ index: index, expr: expr, istrue: Function(`${variables} if(${temp_expr}){return true}else{return false}`)() });
  }

  Else(index){
    this.branches.push({ index: index });
    return this;
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
