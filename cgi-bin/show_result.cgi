#!/usr/bin/perl

use strict;
use Template;
use Error qw(:try);
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
        data        => undef,
        file_path   => 'data/sync_test.output',
        format      => $format,
    }, 
    {
        id          => 'api_test',
        title       => 'API test results',
        data        => undef,
        file_path   => 'data/api_test.output',
        format      => $format,
    },
];

sub make_graph_data_from_file {
    my ($file_path) = @_;

    my $data = "[['Date', 'OK', 'Not OK', 'Skip', 'Todo']";
    my $file_h;
    try{
        open($file_h, '<', $file_path) or die 'Cannot open the input file.';
        while(my $line = <$file_h>) {
            $data .= ', ';
            $data .= '[' . $line . ']';
        }

        $data .= "]";
    }
    finally {
        close $file_h;
        return $data;
    }
}

sub main {
    foreach(@$graphs) {
        $_->{data} = make_graph_data_from_file($_->{file_path});
    }

    my $tt = Template->new({
        INCLUDE_PATH    => './t/',
        ABSOLUTE        => 'true',
    });

    print "Content-type: text/html\n\n";
    $tt->process('graph.tt', {graphs => $graphs});
}

main;
