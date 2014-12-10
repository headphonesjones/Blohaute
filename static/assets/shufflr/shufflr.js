(function($) {

    "use strict";


    var Shufflr, Animations;


    Shufflr = function(element, options) {

        this.options = $.extend({}, Shufflr.defaults, options);

        var $this            = this,
            $element         = $(element);

        if($element.data("shufflr")) return;

        this.element    = $(element);
        this.collection = this.element.find('.shufflr-collection')

        this.element.on('click', '[data-filter]', function(e) {
            e.preventDefault();
            $this.filter($(this).data('filter'));
        });

        this.filter(this.options.filter, true);

        this.element.data("shufflr", this);
    };

    // Class definition
    Shufflr.prototype = {

        filter: function(group, noeffect) {

            group = group ? group.split(',') : [];

            var $this     = this,
                items     = this.collection.children(),
                height    = this.collection.height(),
                animClass = 'animated ' + this.options.animation,
                filtered  = [];

            if(!noeffect) this.collection.css('height', height);

            if (group.length) {

                group = trimArrayItems(group);

                items.each(function(){

                    var item   = $(this),
                        igroup = item.data('group');

                    if(igroup) {

                        igroup = trimArrayItems(igroup.split(','));

                        for (var i=0;i<igroup.length;i++) {
                            if ($.inArray(igroup[i], group)!=-1) {
                                filtered.push(this);
                            } else {
                                item.hide();
                            }
                        }
                    }
                });

            } else {

                items.each(function(){
                    filtered.push(this);
                });
            }

            if (filtered.length) {

                filtered = $(filtered);


                if (noeffect) {
                    filtered.show();
                    return;
                }

                filtered.removeClass(animClass).css('visibility', 'hidden').show();

                var last = filtered.last();

                height = (last.offset().top - this.collection.offset().top) + last.outerHeight();

                items.hide();

                this.collection.animate({'height':height}, function(){

                    filtered.css('visibility', '').addClass(animClass).width(); // force redraw

                    setTimeout(function(){
                        filtered.show();
                        $this.collection.css('height', '');
                    }, 0)
                });

            }

        }
    };


    Animations = {

    };

    Shufflr.animations = Animations;

    Shufflr.defaults = {
        animation : "bounce",
        filter: ''
    };


    function trimArrayItems(arr) {

        for (var i=0;i<arr.length;i++) {
            arr[i] = $.trim(arr[i]);
        }

        return arr;
    }

    function parseoptions(string) {

        if ($.isPlainObject(string)) return string;

        var start = (string ? string.indexOf("{") : -1), options = {};

        if (start != -1) {
            try {
                options = (new Function("", "var json = " + string.substr(start) + "; return JSON.parse(JSON.stringify(json));"))();
            } catch (e) {}
        }

        return options;
    };


    // init code

    function init() {
        $("[data-shufflr-init]").each(function() {

            var shufflr = $(this);

            if (!shufflr.data("shufflr")) {
                var obj = new Shufflr(shufflr, parseoptions(shufflr.attr('data-shufflr-init')));
            }
        });
    }

        // helper

    function parseoptions(string) {

        if ($.isPlainObject(string)) return string;

        var start = (string ? string.indexOf("{") : -1), options = {};

        if (start != -1) {
            try {
                options = (new Function("", "var json = " + string.substr(start) + "; return JSON.parse(JSON.stringify(json));"))();
            } catch (e) {}
        }

        return options;
    };

    function debounce(func, wait, immediate) {
        var timeout;
        return function() {
            var context = this, args = arguments;
            var later = function() {
                timeout = null;
                if (!immediate) func.apply(context, args);
            };
            var callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func.apply(context, args);
        };
    };


    if(!window.MutationObserver) {

        try {

            var observer = new MutationObserver(debounce(function(mutations) {
                init();
            }, 50));

            // pass in the target node, as well as the observer options
            observer.observe(document.body, { childList: true, subtree: true });

        } catch(e) {}
    }

    $(init);

})(jQuery);
