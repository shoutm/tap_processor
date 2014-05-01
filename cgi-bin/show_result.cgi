#!/usr/bin/perl

use strict;
use Template;
use Data::Dumper;
use Error qw(:try);
use JSON qw(encode_json);
use Storable qw(dclone);
use CGI;

our $q;
our $format = encode_json([
    {   #ok
        color => 'blue',
    },
    {   #not_ok
        color => 'red',
    },
    {   #skip
        color => 'yellow',
    },
    {   #todo
        color => 'green',
    },
]);

# This directory includes tap result files which name ends with .csv
our $tap_result_dir = '/var/lib/jenkins/tap_results/';
our $DEFAULT_DISPLAY_ROW_NUM = 30;

sub make_graph_data_from_file {
    my ($file_path, $display_row_num) = @_;

    my $data = [['Date', 'OK', 'Not OK', 'Skip', 'Todo', 'Coverage']],
    my $file_h;
    open($file_h, '<', $file_path) or die 'Cannot open the input file.';
    while(my $line = <$file_h>) {
        my $row = []; 
        my @elements = split(',', $line);
        my $total = 0; # Total number of tests

        # Date
        my $date = shift @elements;
        push @$row, $date;

        # OK
        my $ok = shift @elements;
        push @$row, int($ok);
        $total += $ok;

        # Other
        foreach my $elm (@elements) {
          push @$row, int($elm); 
          $total += int($elm);
        }

        # Push OK coverage
        my $coverage;
        if($total == 0) {
            $coverage = 0;
        }
        else {
            $coverage = int($ok / $total * 100);
        }       
        push @$row, $coverage; 

        push @$data, $row;
    }

    my $descending_data = reverse_data_rows($data);
    my @result = @{$descending_data}[0..$display_row_num];

    close $file_h;
    return \@result;
}

sub convert_chartdata_to_graphdata {
    my ($data) = @_;

    my $reversed_chart_data = reverse_data_rows($data);

    my $graph_data = [];
    foreach(@$reversed_chart_data) {
        pop @$_; # drop coverage column
        push @$graph_data, $_;
    }

    return $graph_data;
}

sub reverse_data_rows {
    my ($data) = @_;

    my @chart_data = @{ dclone($data) };
    my $title_row = shift @chart_data;

    my @reversed_chart_data = reverse @chart_data;
    unshift @reversed_chart_data, $title_row;

    return \@reversed_chart_data;
}

sub main {
    $q = CGI->new;

    my $display_row_num = $q->param('max-rows') || $DEFAULT_DISPLAY_ROW_NUM;

    opendir(DIR, $tap_result_dir) || die $!;
    my $graphs = [];
    while (my $file_name = readdir(DIR)) {
        next if $file_name eq '.' or $file_name eq '..' or $file_name !~ /.csv$/;
        my $graph_item = {};
        my $file_name_without_ext = $file_name;
        $file_name_without_ext =~ s/(.+)\.[^.]+$/$1/x;
        $graph_item->{id} = $file_name_without_ext;
        $graph_item->{title} = 'Test Result: ' .  $file_name_without_ext .
            "(Recent $display_row_num results)";
        $graph_item->{format} = $format;
        $graph_item->{chart_data} = make_graph_data_from_file(
            $tap_result_dir . $file_name, $display_row_num);
        $graph_item->{graph_data} = encode_json(convert_chartdata_to_graphdata(
            $graph_item->{chart_data}));
        push @$graphs, $graph_item;
    }

    my $tt = Template->new({
        INCLUDE_PATH    => './t/',
        ABSOLUTE        => 'true',
    });

    print "Content-type: text/html\n\n";
    $tt->process('graph.tt', {graphs => $graphs});
}

main;
