var ud = ud || {};
var _paq = _paq || [];


class Page {
  content_hash = null
  page_hash = null
  template = null
  replacements = {}
}

(function () {
  let i = 0;
  let page = new Page();
  'use strict';

  function handleAnchors(){ 
    var anchors = document.getElementsByTagName('a');
    for(var i=0;i<anchors.length;i++){
      anchors[i].addEventListener('click', handleClick);
    }
  }

  function handleForms(){ 
    var forms = document.getElementsByTagName('form');
    for(var i=0;i<forms.length;i++){
      forms[i].addEventListener('submit', handleSubmit);
    }
  }

  function handleSubmit(event){
    if(event.target.tagName == 'FORM'){
      var path = localPart(event.target.action);
      if(path.length>0){
        var data = {};
        fetchPage(path, data);        
        event.preventDefault();
      }
    }
  }

  function handleClick(event){
    if(event.target.tagName == 'A'){
      var path = localPart(event.target.href);
      if(path.length>0){
        if(event.altKey){
          //TODO: delete this when done
          path += `?variable=newContent${i}&variable2=moreContent${i}`;
        }else{
          path += '?variable=samecontent&variable2=moresamecontent';
        }
        fetchPage(path);        
        event.preventDefault();
      }
    }
  }
  
  function localPart(url){
    if(url.startsWith(window.location.origin)){
      return url.substring(window.location.origin.length);
    }
    if(url.startsWith('//'+window.location.host)){
      return url.substring(window.location.host.length+2);
    }
    if(url.startsWith('/') && !url.startsWith('//')){
      return url;
    }
    return false;
  }

  function fetchPage(url, data){
    ud.ajax(url, {success: handlePage});
    i++;
  }

  function renderPage(data){
    for(let key in page.replacements){
      data = data.replace(key, page.replacements[key]);
    }
    document.querySelector('html').innerHTML = data;
    handleAnchors();
  }
  
  function handlePage(data){
    //If the page is the same but the content is different we can retrieve the page from the hash and replace the placeholders with new values
    //If the page is different we need to reload everything and update the cache
    if(page.content_hash !== data[2].content_hash){
      console.log('hashes do not match, retrieve new template');
      ud.ajax('/getrawtemplate', {success: renderPage, mimeType: 'text/html'});

      page.page_hash = data[2].page_hash;
      page.content_hash = data[2].content_hash;
      page.replacements = data[2].replacements;
      return
    }
    console.log('hashes match, retrieve shit from cache');
  }
  
  function init(){
    handleAnchors();
  }
 
  init();
 
}());
