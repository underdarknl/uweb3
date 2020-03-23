class Template {  
  get FUNCTION() {
    return /\{\{\s*(.*?)\s*\}\}/mg;
  }

  get TAG() {
    return /(\[\w+(?:(?::[\w-]+)+)?(?:(?:\|[\w-]+(?:\([^()]*?\))?)+)?\])/gm;
  }

  constructor(template, replacements){
    window.global_replacements = replacements;
    this.scopes = [this];
    this.AddString(template);

    this.template = template;
    this.html = template;
    this.replacements = replacements;
    // this.html = []
    // this.parse()
    // this.replacePlaceholders();
  }


  static TagSplit(template) {
    return template.split(Template.prototype.TAG).map((node, index) => {
      if(index % 2) {
        return TemplateTag.FromString(node);
      }else{
        return new TemplateText(node);
      }
    });
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

  append(part) {
    if(this.default){
      self.default.push(part);
    }else{
      self.branches[branches.length][1].append(part);
    }
  }

  _ExtendFunction(nodes) {
    nodes = nodes.split(" ");
    let func = nodes.shift();
    func = func.charAt(0).toUpperCase() + func.substring(1);
    this[`_TemplateConstruct${func}`](nodes);
    // try {
    // } catch (error) {
    //   console.log(`Unknown template function {{ ${func} }}`);
    // }
  }

  _AddToOpenScope(item){
    this.scopes[this.scopes.length  - 1];
  }

  _StartScope(scope){
    this._AddToOpenScope(scope);
    this.scopes.append(scope);
  }

  _ExtendText(nodes){
  }

  _TemplateConstructIf(nodes){
    //Processing for {{ if }} template syntax
    this._StartScope(new TemplateConditional(nodes.join(' ')));
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
  constructor(expr, checking_presence=false) {
    this.checking_presence = checking_presence;
    this.branches = [];
    this.default = null;
    this.NewBranch(expr);
  }

  NewBranch(expr){
    // this.branches.push((Template.TagSplit(expr), []));
    console.log(expr);
    this.branches.push([Template.TagSplit(expr), []]);
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

  PFX_INDEX = ':';
  PFX_FUNCT = '|';
  // FUNC_FINDER = re.compile('\|([\w-]+(?:\([^()]*?\))?)')
  // FUNC_CLOSURE = re.compile('(\w+)\((.*)\)')

  constructor(tag){
    this.value = window.global_replacements[tag]    
  }

  static FromString(tag) {
    return new TemplateTag(tag);
  }
}

// class TemplateConditional {

//   constructor(value, replacements){
//     this.value = value;
//     this.replacements = replacements;
    
//     let variables = ""
//     Object.keys(this.replacements).map((replacement) => {
//       let key = replacement.substr(1, replacement.length - 2);
//       let value = this.replacements[replacement];
//       variables += `let ${key} = '${value}';`;
//     });
//   }
// }

class TemplateLoop {

}

// class TemplateFunction {
//   BODY = /{{(.*?)}}/gm;
//   lookup = {
//     'if': TemplateConditional,
//     'for': TemplateLoop,
//     'while': TemplateLoop
//   };

//   constructor(value, replacements){
//     this.value = value;
//     this.replacements = replacements;
//     this.findBody();
//     this.function = new this.lookup[this.keyword](this.value, this.replacements);
//   }

//   findBody(){
//     let m;

//     while ((m = this.BODY.exec(this.value)) !== null) {
//         // This is necessary to avoid infinite loops with zero-width matches
//         if (m.index === this.BODY.lastIndex) {
//           this.BODY.lastIndex++;
//         }
        
//         // The result can be accessed through the `m`-variable.
//         m.forEach((match, groupIndex) => {
//           if(groupIndex == 1){
//             //Deterime the templatefunction type we are dealing with
//             if(!this.keyword){
//               this.keyword = match.split(" ").filter(Boolean)[0];
//             }
//             // console.log(`Found match: ${match} type: ${this.keyword}`);
//           }
//         });
//     }

//   }
// }

