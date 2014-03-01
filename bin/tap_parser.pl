#!/usr/bin/perl
package TapParser;

use strict;
use Error qw(:try);
use Data::Dumper;
use POSIX qw(strftime);

our $target = [
    {   # ok
        include => '^ok',
        exclude => '# skip',
        count   => 0, },
    {   # not ok
        include => '^not ok',
        exclude => '# TODO & SKIP',
        count   => 0, },
    {   # skip
        include => '^ok.*# skip',
        count   => 0, },
    {   # todo skip
        include => '^not ok.*# TODO & SKIP',
        count   => 0, },
];

sub parse_line {
    my ($line) = @_;

    foreach(@$target) {
        if( ($line =~ /$_->{include}/) and
            (!defined $_->{exclude} or
             $line !~ /$_->{exclude}/)) {
            $_->{count}++;
        }
    }
}

sub parse_file {
    my ($file_path) = @_;

    my $file_h;
    try {
        open($file_h, "<", $file_path) or die 'Cannot open the input file.';
        while(my $line = <$file_h>) {
            parse_line $line;
        }
    } 
    finally {
        close $file_h;
    }
}

sub output_str {
    my $output_str = '';
    $output_str .= "'" . strftime("%Y/%m/%d-%H:%M", localtime) . "'";
    foreach(@$target) {
        $output_str .= ", ";
        $output_str .= $_->{count};
    }
    $output_str .= "\n";

    return $output_str;
}

sub output_result {
    my ($output_file_path, $output_str) = @_;

    my $file_h;
    try {
        open($file_h, ">>", $output_file_path)
            or die 'Cannot open the input file.';
        print $file_h $output_str;
    } 
    finally {
        close $file_h;
    }
}

sub main {
    my ($output_file_path, @file_paths) = @ARGV;

    if(!defined $output_file_path) {
        my $help = <<END;
Usage: ./tap_parser.pl <output_file_path> <tap1> <tap2> ...
This script reads tap files and count numbers of ok, not_ok, etc in 
each top subtests in each files. Then it appends one line which contains
the numbers of them to the specified file. 
END
        print $help;
        return;
    }

    foreach(@file_paths) {
        parse_file $_;
    }

    output_result($output_file_path, output_str);
}

main;
