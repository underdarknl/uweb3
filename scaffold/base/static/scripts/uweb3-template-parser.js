class Template {  
  openScopes = [];

  get FUNCTION() {
    return /\{\{\s*(.*?)\s*\}\}/mg;
  }

  get TAG() {
    return /(\[\w+(?:(?::[\w-]+)+)?(?:(?:\|[\w-]+(?:\([^()]*?\))?)+)?\])/gm;
  }

  constructor(template, replacements){
    window.replacements = replacements;
    this.inForLoop = false;
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

  AddString(template) {
    let nodes = template.split(this.FUNCTION);
    nodes.map((node, index) => {
      let tmp_node = node.split(" ");
      let func = tmp_node.shift();
      func = func.charAt(0).toUpperCase() + func.substring(1);

      if(index % 2){
        this._ExtendFunction(func, tmp_node, index);
      }else{
        this._ExtendText(node, index)
      }
    });
    console.log(this.scopes);
    console.log(this.tmp);
    this._EvaluateScope();
  }
  _EvaluateScope(){
    this.scopes.map((object, index) => {
      console.log(object);
      // let deleteScopes = false;
      // for(let branch in object.branches){
      //   if(!object.branches[branch].istrue){
      //     //Delete all the scopes from which the condition was not met
      //     if(object.branches[branch].istrue !== undefined || deleteScopes){
      //       //If the branch returns undefined its the last clause in the if statement so it will always be true
      //       delete this.tmp[object.branches[branch].index + 1];
      //     }
      //   }else{
      //     deleteScopes = true;
      //   }
      // }
    });
  }
  _ExtendFunction(func, nodes, index) {
    this[`_TemplateConstruct${func}`](nodes, index);
  }

  _AddToOpenScope(item){
    // this.scopes[this.scopes.length  - 1];
  }

  _StartScope(scope){
    if(this.openScopes.length > 0){
      this.openScopes[this.openScopes.length - 1].branches.push(scope);
    }else{
      this.scopes.push(scope);
    }
  }

  _ExtendText(nodes, index){
    this.tmp[index] = { nodes: nodes };
  }

  _TemplateConstructIf(nodes, index){
    //Processing for {{ if }} template syntax
    this._StartScope(new TemplateConditional(nodes.join(' '), index));
  }

  _TemplateConstructFor(nodes, index){
    let template = new TemplateLoop(nodes.join(' '), index);
    if(this.openScopes.length > 0){
      this.openScopes.push(template);
    }else{
      // this.scopes.push(template);
      this.openScopes.push(template);
    }
  }

  _TemplateConstructEndfor(nodes, index){
    // this.openScopes[this.openScopes.length - 1].branches.push({index: index});
    this.scopes.push(this.openScopes[this.openScopes.length - 1]);
    this.openScopes.pop();
  }

  _TemplateConstructElif(nodes, index){
    this.scopes[this.scopes.length - 1] = this.scopes[this.scopes.length - 1].Elif(index, nodes.join(' '))
  }
  _TemplateConstructElse(nodes, index){
    //Processing for {{ else }} template syntax.
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
    this.NewBranch(expr, index);
  }
  
  NewBranch(expr, index){
    let isTrue = this._EvaluateClause(expr);
    this.branches.push({ index: index, expr: expr });
  }

  _EvaluateClause(expr){
    expr = expr.replace(" and ", " && ");
    expr = expr.replace(" or ", " || ");
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
          temp_expr = expr.split(value).join(value.substring(1, value.length - 1));
        }else{
          temp_expr = expr.split(value).join(window.replacements[value]);
        }
      });
    }
    return Function(`${variables} if(${temp_expr}){return true}else{return false}`)()
  }
  
  Elif(index, expr){
    let isTrue = this._EvaluateClause(expr);
    this.branches.push({ index: index, expr: expr, istrue: isTrue });
    return this;
  }
  
  Else(index){
    this.branches.push({ index: index });
    return this;
  }
}

class TemplateLoop {
  constructor(expr, index) {
    this.branches = [];
    this.NewBranch(expr, index);
  }

  NewBranch(expr, index){
    this.branches.push({ index: index, expr: expr});
  }
}