#!/usr/bin/perl
use strict;
use warnings;

my @netmask1 = qw / 255 /;
my @netmask2 = qw/ 255 /;
my $count = shift or Usage();
while ( $count-- > 0 ) {
 my @ip = ( int(rand(223))+1, # 1 to 223
  int(rand(256)), # 0 to 255
  int(rand(256)), # 0 to 255
  int(rand(0)) # 0 to 255
 );
 my @mask = ( 0, 0, 0, 0 );
  $mask[0] = $netmask1[ int(rand(@netmask1)) ];
   if ( $mask[0] == 255 ) {
    foreach my $idx ( 1..2 ) {
     $mask[$idx] = $netmask2[ int(rand(@netmask2)) ];
    last unless $mask[$idx] == 255;
  }
 }

print "router static address-family ipv4 unicast ", join( ".", @ip), " ", join( ".", @mask), " null0\n";
}
sub Usage {
 print "$0 <number of ip routes to generate>\n";
 exit;
}
