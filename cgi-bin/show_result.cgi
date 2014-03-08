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
        my $coverage = int($ok / $total * 100);
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
    foreach(@$graphs) {
        $_->{chart_data} = make_graph_data_from_file($_->{file_path});
        $_->{graph_data} = encode_json(convert_chartdata_to_graphdata($_->{chart_data}));
    }

    my $tt = Template->new({
        INCLUDE_PATH    => './t/',
        ABSOLUTE        => 'true',
    });

    print "Content-type: text/html\n\n";
    $tt->process('graph.tt', {graphs => $graphs});
}

main;
