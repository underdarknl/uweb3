var ud = ud || {};
var _paq = _paq || [];


class Page {
  html = null

  constructor(page){
    this.page_hash = page[2].page_hash;
    this.content_hash = page[2].content_hash;
    this.template = page[2].template;
    this.replacements = page[2].replacements;
  }
  
}

(function () {
  'use strict';
  let i = 0;
  let cacheHandler = {
    previous_key: null,
    create: function(page){
      if(this.cacheSize() >= 5){
        this.delete(0);
      }
      window.localStorage.setItem(page.page_hash, 
      JSON.stringify({
        'created': new Date().getTime(),
        'content_hash': page.content_hash,
        'replacements': page.replacements,
        'template': page.template, 
        'html': page.html
      }));
      this.previous_key = page.page_hash;
      return 200
    },
    insertHTML: function(html){
      if(this.previous_key){
        let storedPage = this.read(this.previous_key);
        if(!storedPage.html){
          storedPage.html = html;
          window.localStorage.setItem(this.previous_key, JSON.stringify(storedPage));
        }
        return storedPage;
      }
    },
    read: function(page_hash){
      return JSON.parse(window.localStorage.getItem(page_hash));
    },
    delete: function(index){
      let key = window.localStorage.key(index);
      let oldest_item = {
        created: null,
        key: null
      }
      if(index === 0){
        const items = { ...localStorage };
        for(let item in items){
          let current = this.read(item);
          if(current.created < oldest_item.created || oldest_item.created == null){
            oldest_item.created = current.created;
            oldest_item.key = item;
          }
        }
        return window.localStorage.removeItem(oldest_item.key);
      }
      window.localStorage.removeItem(key);
    },
    cacheSize: function(){
      return window.localStorage.length;
    }
  }

  cacheHandler.delete(0);
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
          path += `&variable=newContent${i}&variable2=moreContent${i}`;
        }else{
          path += '&variable=samecontent&variable2=moresamecontent';
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
    ud.ajax(url, { success: handlePage });
    i++;
  }

  function handleReplacements(html, replacements){
    for(let placeholder in replacements){
      html = html.replace(placeholder, replacements[placeholder]);
    }
    return html;
  }

  function handlePage(data, url){
    //If the page is the same but the content is different we can retrieve the page from the hash and replace the placeholders with new values
    //If the page is different we need to reload everything and update the cache
    //Create a new instance of the page object. This only happends on the first call.
    if(url.split('?').length >= 2){
      // console.log(url);
      url = url.split('?')[1];
    }
    if(typeof data === 'object'){
      const { content_hash, page_hash } = data[2];
      const cached = cacheHandler.read(page_hash);
      if(cached){
        if(cached.content_hash === content_hash){
          console.log(`Retrieving page from hash: ${page_hash} with content hash: ${content_hash}`);
          let template = new Template(cached.html, cached.replacements);
          document.querySelector('html').innerHTML = template.template;
        }else{
          console.log(`Retrieving page from hash: ${page_hash} with content hash: ${content_hash}`);
          let template = new Template(cached.html, data[2].replacements);
          document.querySelector('html').innerHTML = template.template;
        }
      }else{
        //If there is no cached page...
        cacheHandler.create(new Page(data));
        return ud.ajax(`/getrawtemplate?${url}&content_hash=${data[2].content_hash}`,  {success: handlePage, mimeType: 'text/html'});
        
      }
    }else if(typeof data === 'string'){
      let html = cacheHandler.insertHTML(data);
      let template = new Template(html.html, html.replacements);

      document.querySelector('html').innerHTML = template.template;
    }
    handleAnchors();
  }
  
  function init(){
    handleAnchors();
  }
 
  init();
 
}());
