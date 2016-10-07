'use strict';

var gulp = require('gulp');
var $ = require('gulp-load-plugins')();

var runSequence = require('run-sequence');
var del = require('del');
var fs = require('fs');

var
  source = 'source/',
  dest = 'dest/';

var scss = {
  sassOpts: {
    outputStyle: 'nested',
    precison: 3,
    errLogToConsole: true,
    includePaths: [
      './node_modules/bootstrap-sass/assets/stylesheets',
      './node_modules/font-awesome/scss/'
    ]
  }
};


// fonts
var fonts = {
  in: [
    source + 'fonts/*.*',
    './node_modules/bootstrap-sass/assets/fonts/bootstrap/*',
    './node_modules/font-awesome/fonts/*'
  ],
  out: 'fonts/'
};

/**
 * Tasks
 * Allow add filter
 *
 */
gulp.task('watch', function (cb) {
  $.watch(source + '/sass/**/*.scss', function () {
    gulp.start('compile-styles');
  });
});

// copy font
gulp.task('fonts', function () {
  return gulp
    .src(fonts.in)
    .pipe(gulp.dest(fonts.out));
});

// = Main tasks
gulp.task('build', function (cb) {
  return runSequence(
    'compile-styles',
    cb
    );
});

// = Build Style
gulp.task('compile-styles', ['fonts'], function (cb) {
  return gulp.src([
    source + '/sass/*.scss',
    '!'+ source +'/sass/_*.scss'
  ])
  .pipe($.sourcemaps.init())
  .pipe($.sass(scss.sassOpts)
    .on('error', $.sass.logError))
  .pipe($.autoprefixer('last 2 versions'))
  .pipe($.concat('style.css'))
  .pipe($.sourcemaps.write('./', {
    includeContent: false,
    sourceRoot: source + '/sass'
  }))
  .pipe(gulp.dest('css'))
});

// ================ Develop
gulp.task('dev', function (cb) {
  return runSequence(
    'build',
    [
    'watch'
    ],
    cb
    );
});
