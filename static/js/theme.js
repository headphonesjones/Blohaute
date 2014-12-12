jQuery(function($) {

    "use strict";

	/*
     * Split nav
     */

    $.UIkit.$win.on('load resize orientationchange', (function(){

        var fn = function() {

            var logowidth   = $('.bh-logo').width(),
                nav         = $('.bh-navbar .uk-navbar-nav'),
                navwrap     = $('.bh-navbar-nav-wrapper'),
                navitems    = nav.children(),
                equal       = Math.ceil(navitems.length / 2),
                rtl         = ($.UIkit.langdirection == 'right'),
                movenav     = 0;

                navwrap.css('visibility', 'hidden');

            navwrap.css({ 'margin-right':'', 'margin-left':'' });
            navitems.eq(equal - 1).css({ 'margin-right':'', 'margin-left':'' });

            for( var i = 0; i < equal; i++ ) {
                movenav += navitems.eq(i).width();
            }

            movenav = (navwrap.width() - movenav) - movenav;

            navwrap.css(rtl ? 'margin-right' : 'margin-left', movenav);
            navitems.eq(equal - 1).css(rtl ? 'margin-left' : 'margin-right', logowidth + 10);

            setTimeout(function(){
                navwrap.css('visibility', '');
            }, 150);

            return fn;
        };

        return fn();

    })());
	
    /*
     * Search Focus
     */

    $('.bh-search-toggle').on('click', function(){
        setTimeout(function(){
            $('.bh-search-bar input:first').focus();
        }, 50);
    });

    /*
     * Slick Slider
     */

    $('.slick-slider').slick({
        dots: false,
        infinite: true,
        speed: 500,
        slidesToShow: 3,
        slidesToScroll: 1,
        responsive: [
            {
              breakpoint: 960,
              settings: {
                arrows: false,
                slidesToShow: 2
              }
            },
            {
              breakpoint: 480,
              settings: {
                arrows: false,
                slidesToShow: 1
              }
            }
          ]
    }).attr('data-uk-check-display', 1).on('uk.check.display', function() {
        this.slick.refresh();
    });

    /*
     * Counter
     */

    if(window.countUp) {

        $('[data-count-up]').each(function(){

            var ele       = $(this),
                options   = $.UIkit.Utils.options(ele.attr('data-count-up')) || {},
                counter   = new countUp(this, options.start || 0, options.end || 100, 0, options.duration || 1.5, options);

            ele.on('uk.scrollspy.inview', function(){
                counter.start();
            });

            var scrollspy = $.UIkit.scrollspy(ele);
        });
    }
    

});


