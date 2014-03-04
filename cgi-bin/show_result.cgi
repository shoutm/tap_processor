#!/usr/bin/perl

use strict;
use Template;
use JSON qw(encode_json);

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
our $graphs = [
    {
        id          => 'sync_test',
        title       => 'Sync test results',
        file_path   => '/var/lib/jenkins/tap_results/sync_test.csv',
        format      => $format,
    }, 
    {
        id          => 'api_test',
        title       => 'API test results',
        file_path   => '/var/lib/jenkins/tap_results/api_test.csv',
        format      => $format,
    },
    {
        id          => 'orchestrator_test',
        title       => 'Orchestrator test results',
        file_path   => '/var/lib/jenkins/tap_results/orchestrator_test.csv',
        format      => $format,
    },
];

sub make_graph_data_from_file {
    my ($file_path) = @_;

    my $data = [['Date', 'OK', 'Not OK', 'Skip', 'Todo']],
    my $file_h;
    open($file_h, '<', $file_path) or die 'Cannot open the input file.';
    while(my $line = <$file_h>) {
        my $row = []; 
        my @elements = split(',', $line);
        my $date = shift @elements;
        push @$row, $date;
        foreach my $elm (@elements) {
          push @$row, int($elm); 
        }
        push @$data, $row;
    }
    close $file_h;
    return $data;
}

sub main {
    foreach(@$graphs) {
        $_->{data} = make_graph_data_from_file($_->{file_path});
        $_->{data_json} = encode_json($_->{data});
    }

    my $tt = Template->new({
        INCLUDE_PATH    => './t/',
        ABSOLUTE        => 'true',
    });

    print "Content-type: text/html\n\n";
    $tt->process('graph.tt', {graphs => $graphs});
}

main;
