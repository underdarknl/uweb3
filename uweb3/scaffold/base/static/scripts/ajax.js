var ud = ud || {};

ud.ajax = (function () {
  'use strict';
  var MAX_CONNECTIONS_PER_HOSTNAME = 6;
  var request = {
    id: 0,
    type: 'update',
    method: 'get',
    url: '',
    data: {},
    mimeType: 'application/json',
    contentType: 'application/x-www-form-urlencoded; charset=UTF-8',
    form: null,
    hostname: '',
    pollDelay: 3000,
    xhr: {},

    change: null,
    success: null,
    error: null,

    create: function (url, settings) {
      var that = Object.create(this);

      that.url = url;
      that.extend(settings);
      that.setUpXhr();
      return that;
    },

    extend: function (props) {
      for (var prop in props) {
        if (props.hasOwnProperty(prop)) {
          this[prop] = props[prop];
        }
      }
    },

    setUpXhr: function () {
      this.xhr = new window.XMLHttpRequest();
      if (this.xhr.overrideMimeType) {
        this.xhr.overrideMimeType(this.mimeType);
      }
      this.xhr.onreadystatechange = this.handleReadyStateChange.bind(this);
    },

    send: function () {
      var query = this.form ? this.getFormDataString() : this.getQueryString();
      var body = null;

      if (query) {
        if (this.method === 'get') {
          this.url += '?' + query;
        }
        if (this.method === 'post') {
          body = query;
        }
      }
      this.xhr.open(this.method, this.url, true);
      this.xhr.setRequestHeader('Content-type', this.contentType);
      this.xhr.setRequestHeader('X-CSRF-Token', csrf.token);
      this.xhr.setRequestHeader('HTTP_X_REQUESTED_WITH', 'xmlhttprequest');
      this.xhr.send(body);
    },

    handleReadyStateChange: function () {
      if (this.change) {
        this.change(this);
      }
      if (this.xhr.readyState === 4) {
        if(this.mimeType === 'application/json'){
          if (this.xhr.status === 200 && this.success) {
            this.success(JSON.parse(this.xhr.responseText));
          } else if (this.error) {
            this.error(this.xhr);
          }
        }else{
          this.success(this.xhr.responseText)
        }
        if (this.type === 'update') {
          this.remove();
        }
      }
    },

    getHostname: function () {
      var parser;

      if (!this.hostname) {
        parser = document.createElement('a');
        parser.href = this.url;
        this.hostname = parser.hostname;
      }
      return this.hostname;
    },

    getQueryString: function (data) {
      var list = [];

      data = data || this.data;
      for (var name in data) {
        if (data[name] instanceof Array) {
          data[name] = data[name].join(',');
        }
        list.push(window.encodeURIComponent(name) + '=' +
          window.encodeURIComponent(data[name])
        );
      }
      return list.join('&');
    },

    getFormDataString: function () {
      var els = this.form.elements;
      var data = {};

      for (var i = 0; i < els.length; i++) {
        if (els[i].name) {
          data[els[i].name] = els[i].value;
        }
      }
      return this.getQueryString(data);
    }
  };

  var overrides = {
    active: {},

    add: function (req) {
      var active = this.active[req.url];

      if (active && active.xhr.readyState !== 4) {
        active.xhr.abort();
      }
      req.send();
      this.active[req.url] = req;
    }
  };

  var updates = {
    active: {},
    queue: {},

    add: function (req) {
      var hostname = req.getHostname();
      var active = this.active[hostname] || [];
      var queue = this.queue[hostname] || [];

      if (active.length < MAX_CONNECTIONS_PER_HOSTNAME) {
        req.send();
        active.push(req);
      } else {
        queue.push(req);
      }
      req.remove = this.remove.bind(this, req);
      this.active[hostname] = active;
      this.queue[hostname] = queue;
    },

    remove: function (req) {
      var hostname = req.getHostname();
      var active = this.active[hostname];
      var next = this.queue[hostname].shift();

      if (next) {
        next.send();
        active.push(next);
      }
      active.splice(active.indexOf(req), 1);
      this.active[hostname] = active;
    }
  };

  var polls = {
    active: {},
    interval: {},

    add: function (req) {
      var interval = this.interval[req.url];

      if (!interval) {
        req.send();
        req.remove = this.remove.bind(this, req);
        interval = window.setInterval(req.send.bind(req), req.pollDelay);
        this.interval[req.url] = interval;
        this.active[req.url] = req;
      }
    },

    remove: function (req) {
      var interval = this.interval[req.url];

      window.clearInterval(interval);
      delete this.active[req.url];
    }
  };

  var proxy = {
    types: {
      override: overrides,
      update: updates,
      poll: polls
    },
    count: 0,

    add: function (req) {
      req.id = ++this.count;
      this.types[req.type].add(req);
    }
  };

  var csrf = {
    token: null,

    handle: function (success, data) {
      this.token = data.token;
      success();
    }
  };

  return function (url, settings) {
    if (typeof url === 'object' && typeof settings === 'undefined') {
      settings = url;
      settings.method = settings.form.method;
      url = settings.form.action;
    }
    if (url === '/csrf') {
      settings.type = 'poll';
      settings.pollDelay = 1000 * 60 * 59;
      settings.success = csrf.handle.bind(csrf, settings.success);
    }
    proxy.add(request.create(url, settings));
  };
}());
