#!/usr/bin/perl

use strict;
use Template;
use Data::Dumper;
use Error qw(:try);
use JSON qw(encode_json);
use Storable qw(dclone);

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

sub make_graph_data_from_file {
    my ($file_path) = @_;

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
    close $file_h;
    return $data;
}

sub convert_chartdata_to_graphdata {
    my ($data) = @_;

    my @chart_data = @{ dclone($data) };

    my $graph_data = [];
    foreach(@chart_data) {
        pop @$_; # drop coverage column
        push @$graph_data, $_;
    }

    return $graph_data;
}

sub main {
    opendir(DIR, $tap_result_dir) || die $!;
    my $graphs = [];
    while (my $file_name = readdir(DIR)) {
        next if $file_name eq '.' or $file_name eq '..' or $file_name !~ /.csv$/;
        my $graph_item = {};
        my $file_name_without_ext = $file_name;
        $file_name_without_ext =~ s/(.+)\.[^.]+$/$1/x;
        $graph_item->{id} = $file_name_without_ext;
        $graph_item->{title} = 'Test Result: ' .  $file_name_without_ext;
        $graph_item->{format} = $format;
        $graph_item->{chart_data} = make_graph_data_from_file(
            $tap_result_dir . $file_name);
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
